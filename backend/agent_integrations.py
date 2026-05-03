# backend/agent_integrations.py
import os
import json
import logging
import requests
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic()

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'

def _log_token_usage(model: str, input_tokens: int, output_tokens: int, cache_read_tokens: int = 0, cache_creation_tokens: int = 0) -> None:
    """Log token usage to database for cost tracking."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO token_usage
            (session_id, model, input_tokens, output_tokens, cache_read_tokens, cache_creation_tokens, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'mission-control',
            model,
            input_tokens,
            output_tokens,
            cache_read_tokens,
            cache_creation_tokens,
            int(time.time() * 1000)
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"Failed to log token usage: {e}")

def score_finding_with_claude(finding_text: str, agent_name: str) -> int:
    """
    Use Claude to score a finding 1-10 based on business impact, urgency, cost.
    Returns integer 1-10.
    """
    try:
        prompt = f"""You are a research agent evaluating business findings. Score this finding 1-10 based on:
- Business impact: Will this affect decisions/strategy?
- Urgency: How time-sensitive is this?
- Cost: Does this affect revenue/spending?

Finding: {finding_text}
Agent: {agent_name}

Respond with ONLY a number 1-10 and brief reasoning (2-3 words max).
Format: "8 - High impact" """

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Log token usage
        _log_token_usage(
            model="claude-haiku-4-5-20251001",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_tokens=getattr(response.usage, 'cache_read_input_tokens', 0),
            cache_creation_tokens=getattr(response.usage, 'cache_creation_input_tokens', 0)
        )

        # Parse response - extract first number
        text = response.content[0].text.strip()
        score = int(text.split()[0])

        # Clamp to 1-10
        score = max(1, min(10, score))
        logger.info(f"Scored finding: {score}/10")
        return score
    except Exception as e:
        logger.error(f"Error scoring finding: {e}")
        # Default to 5 if scoring fails
        return 5

def examine_findings_with_claude(findings: list) -> Dict[int, Dict[str, Any]]:
    """
    Use Claude to examine multiple findings and create gameplans.

    Args:
        findings: List of dicts with id, finding_text, importance_score, category

    Returns:
        Dict mapping finding_id to {analysis, gameplan, priority, needs_approval}
    """
    try:
        # Format findings for Claude
        findings_json = json.dumps([
            {
                'id': f.get('id'),
                'finding': f.get('finding_text'),
                'importance': f.get('importance_score'),
                'category': f.get('category')
            }
            for f in findings
        ], indent=2)

        prompt = f"""Analyze these findings and respond with ONLY a valid JSON object. No markdown, no explanation, no extra text.

For each finding, create an object with:
- "analysis": importance summary
- "gameplan": recommended action
- "priority": critical/high/medium/low
- "needs_approval": true if needs user approval, false if routine
- "trade_action" (ONLY for finance findings with category "trade_signal:*"): {{"ticker": "AAPL", "direction": "buy" or "sell", "confidence": 1-10}}
  - Bullish/positive news = buy. Bearish/risk/downgrade news = sell. Omit for non-finance findings.

Findings JSON:
{findings_json}

Output format (replace finding_id with the actual ID):
{{"finding_id": {{"analysis": "...", "gameplan": "...", "priority": "...", "needs_approval": ...}}, "finding_id": {{"analysis": "...", "gameplan": "...", "priority": "...", "needs_approval": ..., "trade_action": {{"ticker": "...", "direction": "...", "confidence": ...}}}}}}"""

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse JSON response
        text = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text[text.find('\n')+1:]
        if text.endswith("```"):
            text = text[:text.rfind('```')]

        # Try to extract JSON if wrapped in markdown
        if text.startswith('{') and text.endswith('}'):
            # Already valid JSON format
            pass
        else:
            # Try to find JSON within the response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                text = text[start:end]

        result = json.loads(text)

        # Log token usage
        _log_token_usage(
            model="claude-opus-4-7",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_tokens=getattr(response.usage, 'cache_read_input_tokens', 0),
            cache_creation_tokens=getattr(response.usage, 'cache_creation_input_tokens', 0)
        )

        # Convert string keys to integers (Claude returns JSON with string keys)
        result = {int(k): v for k, v in result.items()}

        logger.info(f"Examined {len(result)} findings")
        return result
    except Exception as e:
        logger.error(f"Error examining findings: {e}")
        try:
            logger.debug(f"Claude response text: {text[:500]}")
        except:
            pass
        # Return empty dict if examination fails
        return {}

def send_sms_alert(phone_number: str, finding_text: str, gameplan: str, priority: str) -> bool:
    """
    Send SMS alert via Twilio.

    Args:
        phone_number: User's phone number (E.164 format)
        finding_text: What was found
        gameplan: Recommended action
        priority: critical/high/medium/low

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_from = os.getenv('TWILIO_PHONE_NUMBER')

        if not all([twilio_sid, twilio_token, twilio_from]):
            logger.warning("Twilio credentials not configured")
            return False

        # Construct message
        message = f"""ALERT ({priority.upper()}): {finding_text[:100]}

Gameplan: {gameplan[:150]}

Reply: YES to approve / NO to skip"""

        # Send via Twilio API
        auth = (twilio_sid, twilio_token)
        data = {
            'From': twilio_from,
            'To': phone_number,
            'Body': message
        }

        response = requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json',
            data=data,
            auth=auth,
            timeout=10
        )

        if response.status_code in [200, 201]:
            logger.info(f"SMS sent successfully to {phone_number}")
            return True
        else:
            logger.error(f"Twilio error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False

def call_gm_seat_api(finding: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call GM Seat API to update NFL War Room with finding.

    Args:
        finding: Dict with finding_text, category, importance_score, source_name

    Returns:
        API response dict
    """
    try:
        gm_seat_url = os.getenv('GM_SEAT_API_URL', 'http://localhost:8000/api/war-room/update')

        payload = {
            'finding': finding['finding_text'],
            'category': finding['category'],
            'importance': finding['importance_score'],
            'source': finding['source_name'],
            'recommended_action': finding.get('gameplan', 'Review and assess impact'),
            'timestamp': int(__import__('time').time() * 1000)
        }

        response = requests.post(
            gm_seat_url,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            logger.info(f"GM Seat API updated successfully")
            return response.json()
        else:
            logger.error(f"GM Seat API error: {response.status_code} - {response.text}")
            return {'status': 'error', 'message': 'Failed to update war room'}
    except Exception as e:
        logger.error(f"Error calling GM Seat API: {e}")
        return {'status': 'error', 'message': str(e)}
