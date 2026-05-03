#!/usr/bin/env python3
"""Test script to verify agent pipeline works end-to-end."""

import sys
from pathlib import Path
import sqlite3
import logging
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load env vars
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from agents.research.sports import SportsAgent
from agents.research.finance import FinanceAgent
from agents.examination import ExaminationAgent
from agents.executioner import ExecutionerAgent

DB_PATH = Path.home() / 'Desktop' / 'mission-control' / 'backend' / 'mission_control.db'


def print_section(title):
    """Print a test section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_db_counts():
    """Print counts of records in each table."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    tables = ['research_findings', 'examinations', 'actions']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    conn.close()


def test_rd_agents():
    """Test R&D agents fetching and scoring."""
    print_section("Testing R&D Agents")

    # Test Sports Agent
    print("\n→ Testing Sports Agent...")
    sports = SportsAgent()
    try:
        findings = sports._fetch_findings()
        print(f"  ✓ Fetched {len(findings)} findings")

        if findings:
            print(f"  Processing first finding...")
            sports._process_finding(findings[0])
            print(f"  ✓ Scored and inserted finding")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test Finance Agent
    print("\n→ Testing Finance Agent...")
    finance = FinanceAgent()
    try:
        findings = finance._fetch_findings()
        print(f"  ✓ Fetched {len(findings)} findings")

        if findings:
            print(f"  Processing first finding...")
            finance._process_finding(findings[0])
            print(f"  ✓ Scored and inserted finding")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print("\n→ Database after R&D agents:")
    check_db_counts()


def test_examination_agent():
    """Test examination agent analyzing findings."""
    print_section("Testing Examination Agent")

    exam = ExaminationAgent()

    # Get pending findings count
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM research_findings WHERE status = ?',
                   ('pending_examination',))
    pending_count = cursor.fetchone()[0]
    conn.close()

    print(f"\n→ Pending findings: {pending_count}")

    if pending_count > 0:
        print("→ Running examination agent...")
        try:
            exam._examine_pending_findings()
            print(f"  ✓ Examined findings")
        except Exception as e:
            print(f"  ✗ Error: {e}")

        print("\n→ Database after examination:")
        check_db_counts()
    else:
        print("  (No findings to examine)")


def test_executioner_agent():
    """Test executioner agent processing examinations."""
    print_section("Testing Executioner Agent")

    # Get phone number
    phone = os.getenv("USER_PHONE_NUMBER", "")
    exec_agent = ExecutionerAgent(user_phone_number=phone)

    # Get pending examinations count
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM examinations WHERE status = ?',
                   ('pending_action',))
    pending_count = cursor.fetchone()[0]
    conn.close()

    print(f"\n→ Pending examinations: {pending_count}")

    if pending_count > 0:
        print("→ Running executioner agent...")
        try:
            exec_agent._execute_pending_actions()
            print(f"  ✓ Processed pending actions")
        except Exception as e:
            print(f"  ✗ Error: {e}")

        print("\n→ Database after executioner:")
        check_db_counts()
    else:
        print("  (No examinations to execute)")


def print_sample_data():
    """Print sample findings and examinations."""
    print_section("Sample Data")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Show recent findings
    print("\n→ Recent Research Findings:")
    cursor.execute('''
        SELECT id, agent_name, finding_text, importance_score, status
        FROM research_findings
        ORDER BY created_at DESC
        LIMIT 3
    ''')
    for row in cursor.fetchall():
        text = row['finding_text'][:60] + "..." if len(row['finding_text']) > 60 else row['finding_text']
        print(f"  [{row['id']}] {row['agent_name']:10} score={row['importance_score']} status={row['status']}")
        print(f"       {text}")

    # Show recent examinations
    print("\n→ Recent Examinations:")
    cursor.execute('''
        SELECT id, finding_id, priority, requires_approval, status
        FROM examinations
        ORDER BY created_at DESC
        LIMIT 3
    ''')
    for row in cursor.fetchall():
        approval = "needs approval" if row['requires_approval'] else "autonomous"
        print(f"  [{row['id']}] finding={row['finding_id']} priority={row['priority']} {approval} status={row['status']}")

    # Show recent actions
    print("\n→ Recent Actions:")
    cursor.execute('''
        SELECT id, examination_id, action_type, result
        FROM actions
        ORDER BY created_at DESC
        LIMIT 3
    ''')
    for row in cursor.fetchall():
        print(f"  [{row['id']}] exam={row['examination_id']} type={row['action_type']} result={row['result']}")

    conn.close()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  AGENT PIPELINE SYSTEM TEST")
    print("="*60)

    print(f"\nDatabase: {DB_PATH}")
    print(f"API Key: {'ANTHROPIC_API_KEY' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print(f"NewsAPI: {'NEWSAPI_KEY' if os.getenv('NEWSAPI_KEY') else '❌ Missing'}")
    print(f"Phone:   {os.getenv('USER_PHONE_NUMBER', '❌ Not configured')}")

    # Run tests
    test_rd_agents()
    test_examination_agent()
    test_executioner_agent()
    print_sample_data()

    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
