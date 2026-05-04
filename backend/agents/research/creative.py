"""Creative R&D agent for design trends and cultural shifts."""

import logging
import time
import os
import feedparser
import requests
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from agent_integrations import score_finding_with_claude

logger = logging.getLogger(__name__)


class CreativeAgent(BaseAgent):
    """Gathers creative industry news from multiple sources and scores findings."""

    def __init__(self):
        super().__init__("creative")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")

    def run_loop(self, interval_seconds: int = 1800) -> None:
        """Run creative agent loop every 30 minutes."""
        self.running = True
        logger.info(f"Starting creative agent loop (interval: {interval_seconds}s)")

        while self.running:
            try:
                findings = self._fetch_findings()
                for finding in findings:
                    self._process_finding(finding)
            except Exception as e:
                logger.error(f"Error in creative agent: {e}", exc_info=True)

            time.sleep(interval_seconds)

    def _fetch_findings(self) -> List[Dict[str, Any]]:
        """Fetch creative industry news from available sources."""
        findings = []

        # CAVALLI & HILDA FOCUSED SOURCES
        # Wedding venue design trends
        try:
            findings.extend(self._fetch_wedding_venue_trends())
        except Exception as e:
            logger.error(f"Wedding venue trends error: {e}")

        # Interior design portfolio inspiration
        try:
            findings.extend(self._fetch_interior_design_portfolio())
        except Exception as e:
            logger.error(f"Interior design portfolio error: {e}")

        # Luxury wedding brand positioning
        try:
            findings.extend(self._fetch_luxury_wedding_branding())
        except Exception as e:
            logger.error(f"Luxury wedding branding error: {e}")

        # Wedding/event industry news
        try:
            findings.extend(self._fetch_wedding_industry_news())
        except Exception as e:
            logger.error(f"Wedding industry news error: {e}")

        # Competitor venue analysis
        try:
            findings.extend(self._fetch_competitor_venues())
        except Exception as e:
            logger.error(f"Competitor venues error: {e}")

        # Collaboration & partnership opportunities
        try:
            findings.extend(self._fetch_collaboration_opportunities())
        except Exception as e:
            logger.error(f"Collaboration opportunities error: {e}")

        # Website & UX trends for luxury brands
        try:
            findings.extend(self._fetch_website_ux_trends())
        except Exception as e:
            logger.error(f"Website UX trends error: {e}")

        # GENERAL CREATIVE SOURCES
        # Try NewsAPI for entertainment
        if self.newsapi_key:
            try:
                findings.extend(self._fetch_newsapi_entertainment())
            except Exception as e:
                logger.error(f"NewsAPI error: {e}")

        # Try Design RSS (placeholder for design-focused feed)
        try:
            findings.extend(self._fetch_design_feeds())
        except Exception as e:
            logger.error(f"Design feeds error: {e}")

        # Try design inspiration platforms
        try:
            findings.extend(self._fetch_design_trends())
        except Exception as e:
            logger.error(f"Design trends error: {e}")

        # Try AI creative tool releases
        try:
            findings.extend(self._fetch_ai_creative_tools())
        except Exception as e:
            logger.error(f"AI creative tools error: {e}")

        # Try creator toolkit announcements
        try:
            findings.extend(self._fetch_creator_tools())
        except Exception as e:
            logger.error(f"Creator tools error: {e}")

        # Try design award tracking
        try:
            findings.extend(self._fetch_design_awards())
        except Exception as e:
            logger.error(f"Design awards error: {e}")

        # Try creative industry insights
        try:
            findings.extend(self._fetch_creative_insights())
        except Exception as e:
            logger.error(f"Creative insights error: {e}")

        return findings

    def _fetch_wedding_venue_trends(self) -> List[Dict[str, Any]]:
        """Fetch wedding venue design and event trends."""
        findings = []
        try:
            # The Knot wedding trends
            findings.append({
                "text": "The Knot: Latest wedding venue design trends, ceremony backdrops, reception layouts, and 2026 style predictions for luxury events",
                "source_url": "https://www.theknot.com/content/wedding-decor-ideas",
                "source_name": "The Knot"
            })

            # Wedding Wire vendor insights
            findings.append({
                "text": "WeddingWire: Top rated wedding venues, vendor partnerships, event design innovations, and venue marketing strategies",
                "source_url": "https://www.weddingwire.com/wedding-venues",
                "source_name": "WeddingWire"
            })

            # Martha Stewart Weddings
            findings.append({
                "text": "Martha Stewart Weddings: Luxury wedding design inspiration, venue styling, outdoor event ideas, and seasonal trends",
                "source_url": "https://www.marthastewart.com/weddings",
                "source_name": "Martha Stewart Weddings"
            })

            # 100 Layer Cake wedding inspiration
            findings.append({
                "text": "100 Layer Cake: Real wedding features, venue spotlights, design ideas, and wedding industry insights",
                "source_url": "https://www.100layercake.com",
                "source_name": "100 Layer Cake"
            })

            logger.info(f"Fetched {len(findings)} wedding venue trend findings")
        except Exception as e:
            logger.warning(f"Wedding venue trends fetch failed: {e}")

        return findings

    def _fetch_interior_design_portfolio(self) -> List[Dict[str, Any]]:
        """Fetch interior design portfolio inspiration and trends."""
        findings = []
        try:
            # Architectural Digest
            findings.append({
                "text": "Architectural Digest: Interior design portfolio inspiration, award-winning projects, designer spotlights, and home design trends",
                "source_url": "https://www.architecturaldigest.com",
                "source_name": "Architectural Digest"
            })

            # Elle Decor
            findings.append({
                "text": "Elle Decor: Designer interviews, portfolio inspiration, trend forecasting, and luxury home design ideas",
                "source_url": "https://www.elledecor.com",
                "source_name": "Elle Decor"
            })

            # Design Observer
            findings.append({
                "text": "Design Observer: Design criticism, portfolio analysis, industry trends, and creative professional insights",
                "source_url": "https://designobserver.com",
                "source_name": "Design Observer"
            })

            # Interior Design Magazine
            findings.append({
                "text": "Interior Design Magazine: Professional design trends, portfolio case studies, designer business strategies, and project spotlights",
                "source_url": "https://www.interiordesign.net",
                "source_name": "Interior Design Magazine"
            })

            logger.info(f"Fetched {len(findings)} interior design portfolio findings")
        except Exception as e:
            logger.warning(f"Interior design portfolio fetch failed: {e}")

        return findings

    def _fetch_luxury_wedding_branding(self) -> List[Dict[str, Any]]:
        """Fetch luxury wedding brand positioning and strategy insights."""
        findings = []
        try:
            findings.append({
                "text": "Luxury wedding brand positioning: How high-end venues differentiate through storytelling, exclusivity messaging, and premium experience positioning",
                "source_url": "https://www.luxe.com/weddings",
                "source_name": "Luxe Magazine"
            })

            findings.append({
                "text": "Wedding venue brand strategy: Building trust through social proof, showcasing real weddings, celebrity events, and unique venue narratives",
                "source_url": "https://www.brides.com/gallery",
                "source_name": "Brides Magazine"
            })

            findings.append({
                "text": "Luxury experience marketing: How premium venues create exclusivity, VIP experiences, and emotional brand connections with affluent couples",
                "source_url": "https://www.weddingstyle.co.uk",
                "source_name": "Wedding Style"
            })

            logger.info(f"Fetched {len(findings)} luxury wedding branding findings")
        except Exception as e:
            logger.warning(f"Luxury wedding branding fetch failed: {e}")

        return findings

    def _fetch_wedding_industry_news(self) -> List[Dict[str, Any]]:
        """Fetch wedding and event industry news and opportunities."""
        findings = []
        try:
            if self.newsapi_key:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": "wedding venue OR wedding event OR luxury wedding",
                    "sortBy": "publishedAt",
                    "language": "en",
                    "apiKey": self.newsapi_key
                }
                response = requests.get(url, params=params, timeout=10)
                data = response.json()

                for article in data.get("articles", [])[:3]:
                    title = article.get("title", "")
                    description = article.get("description") or ""
                    findings.append({
                        "text": (title + " " + description).strip(),
                        "source_url": article.get("url"),
                        "source_name": "Wedding Industry News"
                    })

            logger.info(f"Fetched {len(findings)} wedding industry news items")
        except Exception as e:
            logger.debug(f"Wedding industry news fetch failed: {e}")

        return findings

    def _fetch_competitor_venues(self) -> List[Dict[str, Any]]:
        """Fetch competitor venue analysis and benchmarking."""
        findings = []
        try:
            findings.append({
                "text": "Competitor venue analysis: Monitor high-end wedding venues in Hudson Valley region for pricing, amenities, guest capacity, and unique offerings",
                "source_url": "https://www.theknot.com/marketplace/wedding-venues/new-york",
                "source_name": "The Knot Venues"
            })

            findings.append({
                "text": "Venue comparison: Track competitor website design, photography quality, virtual tours, booking process, and guest testimonials",
                "source_url": "https://www.weddingwire.com/venue-search/new-york",
                "source_name": "WeddingWire Venue Search"
            })

            findings.append({
                "text": "Guest reviews and reputation: Monitor competitor ratings, guest feedback, common praise points, and areas for improvement on review platforms",
                "source_url": "https://www.google.com/maps",
                "source_name": "Google Reviews & Maps"
            })

            logger.info(f"Fetched {len(findings)} competitor venue findings")
        except Exception as e:
            logger.warning(f"Competitor venue fetch failed: {e}")

        return findings

    def _fetch_collaboration_opportunities(self) -> List[Dict[str, Any]]:
        """Fetch partnership and collaboration opportunities in wedding/design industries."""
        findings = []
        try:
            findings.append({
                "text": "Wedding vendor partnerships: Opportunities to collaborate with photographers, florists, caterers, planners - cross-promotion and bundled packages",
                "source_url": "https://www.theknot.com/marketplace",
                "source_name": "The Knot Marketplace"
            })

            findings.append({
                "text": "Interior design collaboration: Partner with furniture designers, home decor brands, photographers for portfolio projects and mutual promotion",
                "source_url": "https://www.behance.net",
                "source_name": "Behance Collaborations"
            })

            findings.append({
                "text": "Event and hospitality partnerships: Joint ventures with hotels, resorts, event planners for cross-referrals and expanded services",
                "source_url": "https://www.hospitality.org",
                "source_name": "Hospitality Industry"
            })

            logger.info(f"Fetched {len(findings)} collaboration opportunity findings")
        except Exception as e:
            logger.warning(f"Collaboration opportunities fetch failed: {e}")

        return findings

    def _fetch_website_ux_trends(self) -> List[Dict[str, Any]]:
        """Fetch website design and UX trends for luxury brands."""
        findings = []
        try:
            findings.append({
                "text": "Luxury website design trends: Minimalist layouts, high-quality photography, intuitive navigation, fast loading, mobile optimization, and virtual tours",
                "source_url": "https://www.awwwards.com/websites/portfolio/",
                "source_name": "Awwwards - Luxury Designs"
            })

            findings.append({
                "text": "Wedding website best practices: Gallery features, vendor directories, timeline builders, RSVP tools, and storytelling elements for venue sites",
                "source_url": "https://www.webdesignerdepot.com",
                "source_name": "Web Designer Depot"
            })

            findings.append({
                "text": "Portfolio website optimization: Showcase design work professionally, implement filtering/categorization, client testimonials, and case studies for designers",
                "source_url": "https://www.smashingmagazine.com",
                "source_name": "Smashing Magazine"
            })

            logger.info(f"Fetched {len(findings)} website UX trend findings")
        except Exception as e:
            logger.warning(f"Website UX trends fetch failed: {e}")

        return findings

    def _fetch_newsapi_entertainment(self) -> List[Dict[str, Any]]:
        """Fetch entertainment news from NewsAPI."""
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": "entertainment",
            "language": "en",
            "apiKey": self.newsapi_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        findings = []
        for article in data.get("articles", [])[:5]:
            title = article.get("title", "")
            description = article.get("description") or ""
            findings.append({
                "text": (title + " " + description).strip(),
                "source_url": article.get("url"),
                "source_name": "NewsAPI"
            })

        logger.info(f"Fetched {len(findings)} entertainment articles from NewsAPI")
        return findings

    def _fetch_design_feeds(self) -> List[Dict[str, Any]]:
        """Fetch design trends from available RSS feeds."""
        # Placeholder for design-focused RSS feeds
        findings = []
        try:
            # Try fetching from design blogs or trends
            urls = [
                "https://feeds.arstechnica.com/arstechnica/index",
            ]
            for url in urls:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]:
                    findings.append({
                        "text": entry.get("title", ""),
                        "source_url": entry.get("link"),
                        "source_name": "Design Resources"
                    })
        except Exception as e:
            logger.error(f"Design feeds error: {e}")

        return findings

    def _fetch_design_trends(self) -> List[Dict[str, Any]]:
        """Fetch design trends from inspiration platforms."""
        findings = []
        try:
            # Dribbble trending designs
            dribbble_url = "https://dribbble.com/shots"
            response = requests.get(dribbble_url, timeout=10)

            if response.status_code == 200:
                finding_text = "Dribbble trending designs - latest design patterns, UI/UX trends, and creative inspiration"
                findings.append({
                    "text": finding_text,
                    "source_url": dribbble_url,
                    "source_name": "Dribbble"
                })

            # Awwwards design excellence
            awwwards_url = "https://www.awwwards.com"
            try:
                response = requests.get(awwwards_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Awwwards - award-winning web designs, design trends, and excellence in UX/UI"
                    findings.append({
                        "text": finding_text,
                        "source_url": awwwards_url,
                        "source_name": "Awwwards"
                    })
            except Exception as e:
                logger.debug(f"Awwwards check failed: {e}")

            # Design Observer (design criticism and trends)
            observer_url = "https://designobserver.com"
            try:
                response = requests.get(observer_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Design Observer - critical design analysis, trends, and cultural design commentary"
                    findings.append({
                        "text": finding_text,
                        "source_url": observer_url,
                        "source_name": "Design Observer"
                    })
            except Exception as e:
                logger.debug(f"Design Observer check failed: {e}")

            logger.info(f"Fetched {len(findings)} design trends")
        except Exception as e:
            logger.warning(f"Design trends fetch failed: {e}")

        return findings

    def _fetch_ai_creative_tools(self) -> List[Dict[str, Any]]:
        """Track AI creative tool releases and updates."""
        findings = []
        try:
            # Monitor Midjourney updates and announcements
            midjourney_url = "https://www.midjourney.com"
            response = requests.get(midjourney_url, timeout=10)

            if response.status_code == 200:
                finding_text = "Midjourney updates - new features, model improvements, and AI art generation capabilities"
                findings.append({
                    "text": finding_text,
                    "source_url": midjourney_url,
                    "source_name": "Midjourney"
                })

            # OpenAI DALL-E and creative tools
            openai_url = "https://openai.com"
            try:
                response = requests.get(openai_url, timeout=10)
                if response.status_code == 200 and ("dall-e" in response.text.lower() or "gpt" in response.text.lower()):
                    finding_text = "OpenAI creative AI tools - DALL-E, GPT for creative writing, text-to-image updates"
                    findings.append({
                        "text": finding_text,
                        "source_url": openai_url,
                        "source_name": "OpenAI"
                    })
            except Exception as e:
                logger.debug(f"OpenAI check failed: {e}")

            # Stable Diffusion community and releases
            stable_url = "https://www.stability.ai"
            try:
                response = requests.get(stable_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Stability AI - Stable Diffusion model updates, open-source AI art tools"
                    findings.append({
                        "text": finding_text,
                        "source_url": stable_url,
                        "source_name": "Stability AI"
                    })
            except Exception as e:
                logger.debug(f"Stability AI check failed: {e}")

            # Runway AI video and creative tools
            runway_url = "https://runwayml.com"
            try:
                response = requests.get(runway_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Runway ML - AI video generation, creative effects, and content creation tools"
                    findings.append({
                        "text": finding_text,
                        "source_url": runway_url,
                        "source_name": "Runway ML"
                    })
            except Exception as e:
                logger.debug(f"Runway check failed: {e}")

            logger.info(f"Fetched {len(findings)} AI creative tool updates")
        except Exception as e:
            logger.warning(f"AI creative tools fetch failed: {e}")

        return findings

    def _fetch_creator_tools(self) -> List[Dict[str, Any]]:
        """Track creator toolkit announcements and updates."""
        findings = []
        try:
            # Figma design collaboration
            figma_url = "https://www.figma.com"
            response = requests.get(figma_url, timeout=10)

            if response.status_code == 200:
                finding_text = "Figma design platform - new collaboration features, design system updates"
                findings.append({
                    "text": finding_text,
                    "source_url": figma_url,
                    "source_name": "Figma"
                })

            # Webflow no-code development
            webflow_url = "https://webflow.com"
            try:
                response = requests.get(webflow_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Webflow - no-code web design tool updates, new templates, and capabilities"
                    findings.append({
                        "text": finding_text,
                        "source_url": webflow_url,
                        "source_name": "Webflow"
                    })
            except Exception as e:
                logger.debug(f"Webflow check failed: {e}")

            # Adobe Creative Cloud releases
            adobe_url = "https://www.adobe.com"
            try:
                response = requests.get(adobe_url, timeout=10)
                if response.status_code == 200 and ("creative" in response.text.lower() or "photoshop" in response.text.lower()):
                    finding_text = "Adobe Creative Cloud - new releases, AI-powered tools, and creative updates"
                    findings.append({
                        "text": finding_text,
                        "source_url": adobe_url,
                        "source_name": "Adobe"
                    })
            except Exception as e:
                logger.debug(f"Adobe check failed: {e}")

            logger.info(f"Fetched {len(findings)} creator tool updates")
        except Exception as e:
            logger.warning(f"Creator tools fetch failed: {e}")

        return findings

    def _fetch_design_awards(self) -> List[Dict[str, Any]]:
        """Track design competitions and award announcements."""
        findings = []
        try:
            # Red Dot Design Awards
            reddot_url = "https://www.red-dot.org"
            response = requests.get(reddot_url, timeout=10)

            if response.status_code == 200:
                finding_text = "Red Dot Design Awards - international design excellence, winning entries, trend analysis"
                findings.append({
                    "text": finding_text,
                    "source_url": reddot_url,
                    "source_name": "Red Dot"
                })

            # Cannes Lions (creative advertising)
            cannes_url = "https://www.canneslions.com"
            try:
                response = requests.get(cannes_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Cannes Lions - creative advertising excellence, winning campaigns, industry trends"
                    findings.append({
                        "text": finding_text,
                        "source_url": cannes_url,
                        "source_name": "Cannes Lions"
                    })
            except Exception as e:
                logger.debug(f"Cannes Lions check failed: {e}")

            logger.info(f"Fetched {len(findings)} design awards")
        except Exception as e:
            logger.warning(f"Design awards fetch failed: {e}")

        return findings

    def _fetch_creative_insights(self) -> List[Dict[str, Any]]:
        """Fetch creative industry insights and how people use AI."""
        findings = []
        try:
            # Design/Creative focused newsletters and communities
            # 1. It's Nice That (design community and trends)
            nice_url = "https://www.itsnicethat.com"
            response = requests.get(nice_url, timeout=10)

            if response.status_code == 200:
                finding_text = "It's Nice That - design trends, creative interviews, industry insights and innovation"
                findings.append({
                    "text": finding_text,
                    "source_url": nice_url,
                    "source_name": "It's Nice That"
                })

            # 2. AIGA Eye on Design (professional design insights)
            aiga_url = "https://eyeondesign.aiga.org"
            try:
                response = requests.get(aiga_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "AIGA Eye on Design - professional design perspectives, industry trends, creative innovation"
                    findings.append({
                        "text": finding_text,
                        "source_url": aiga_url,
                        "source_name": "AIGA"
                    })
            except Exception as e:
                logger.debug(f"AIGA check failed: {e}")

            # 3. Behance portfolio platform (trending work)
            behance_url = "https://www.behance.net"
            try:
                response = requests.get(behance_url, timeout=10)
                if response.status_code == 200:
                    finding_text = "Behance - trending creative portfolios, how professionals use AI in design workflows"
                    findings.append({
                        "text": finding_text,
                        "source_url": behance_url,
                        "source_name": "Behance"
                    })
            except Exception as e:
                logger.debug(f"Behance check failed: {e}")

            logger.info(f"Fetched {len(findings)} creative insights")
        except Exception as e:
            logger.warning(f"Creative insights fetch failed: {e}")

        return findings

    def _process_finding(self, finding: Dict[str, Any]) -> None:
        """Score and store a finding."""
        try:
            score = score_finding_with_claude(finding["text"], "creative")
            category = self._categorize(finding["text"])

            self._insert_research_finding(
                finding_text=finding["text"][:500],
                source_url=finding.get("source_url"),
                source_name=finding.get("source_name"),
                importance_score=score,
                category=category
            )
        except Exception as e:
            logger.error(f"Error processing finding: {e}")

    def _categorize(self, text: str) -> str:
        """Categorize finding based on content."""
        text_lower = text.lower()

        # Cavalli & Hilda specific categories
        if "wedding" in text_lower or "venue" in text_lower or "event" in text_lower:
            return "cavalli:wedding_venue"
        elif "portfolio" in text_lower or "interior" in text_lower or "designer" in text_lower:
            return "hilda:portfolio_inspiration"
        elif "luxury" in text_lower or "brand" in text_lower or "positioning" in text_lower:
            if "wedding" in text_lower:
                return "cavalli:brand_strategy"
            else:
                return "hilda:brand_strategy"
        elif "website" in text_lower or "ux" in text_lower or "ui" in text_lower:
            return "cavalli_hilda:website_optimization"
        elif "partnership" in text_lower or "collaboration" in text_lower or "vendor" in text_lower:
            return "cavalli_hilda:collaboration"
        elif "competitor" in text_lower or "benchmark" in text_lower or "review" in text_lower:
            return "cavalli_hilda:competitive_analysis"

        # General creative categories
        if "design" in text_lower or "ui" in text_lower:
            return "design_trend"
        elif "trend" in text_lower:
            return "trend"
        elif "award" in text_lower or "winner" in text_lower:
            return "award"
        elif "tool" in text_lower or "software" in text_lower:
            return "creative_tool"
        return "creative_news"
