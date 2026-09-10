"""
scraper.py - Playwright-based web scraper with content cleaning
Fetches homepage + relevant subpages, returns clean markdown text
"""
import re
import logging
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from markdownify import markdownify as md

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keywords to identify relevant subpages
SUBPAGE_KEYWORDS = ["about", "team", "company", "contact", "pricing", "careers", "leadership", "press"]

class WebScraper:
    def __init__(self, headless=True, max_subpages=4):
        self.headless = headless
        self.max_subpages = max_subpages  # Limit subpages to save tokens
        self.browser = None
        self.context = None

    def __enter__(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.pw:
            self.pw.stop()

    def scrape_domain(self, domain: str) -> dict:
        """
        Main entry: scrape a domain and return combined clean content.
        Returns dict with 'domain', 'pages' (list of {url, content}), and 'error'
        """
        result = {"domain": domain, "pages": [], "error": None}
        base_url = f"https://{domain}" if not domain.startswith("http") else domain

        try:
            # Step 1: Fetch homepage
            logger.info(f"Scraping homepage: {base_url}")
            page = self.context.new_page()
            page.goto(base_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)  # Wait for JS rendering

            self._dismiss_overlays(page)

            homepage_content = self._extract_clean_content(page)
            result["pages"].append({"url": base_url, "content": homepage_content})

            # Step 2: Discover subpages
            subpage_urls = self._discover_subpages(page, base_url)
            logger.info(f"   Found {len(subpage_urls)} relevant subpages: {subpage_urls}")

            # Step 3: Visit each subpage
            for sub_url in subpage_urls[:self.max_subpages]:
                try:
                    logger.info(f"   Scraping subpage: {sub_url}")
                    page.goto(sub_url, wait_until="domcontentloaded", timeout=15000)
                    page.wait_for_timeout(1500)
                    self._dismiss_overlays(page)

                    sub_content = self._extract_clean_content(page)
                    if sub_content and len(sub_content) > 50:  # Skip empty pages
                        result["pages"].append({"url": sub_url, "content": sub_content})
                except (PlaywrightTimeout, Exception) as e:
                    logger.warning(f"   ⚠️ Failed to scrape {sub_url}: {str(e)}")
                    continue  # Never crash on a single subpage

            page.close()

        except PlaywrightTimeout:
            result["error"] = f"Timeout loading {base_url}"
            logger.error(f"❌ Timeout: {base_url}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Error scraping {base_url}: {str(e)}")

        return result

    def _discover_subpages(self, page, base_url: str) -> list:
        """Find internal links matching relevant keywords."""
        try:
            links = page.eval_on_selector_all("a[href]", "els => els.map(el => el.href)")
            base_domain = urlparse(base_url).netloc

            relevant_urls = []
            seen = set()

            for link in links:
                full_url = urljoin(base_url, link)
                parsed = urlparse(full_url)

                # Only same-domain, no duplicates, no files
                if (parsed.netloc == base_domain
                    and full_url not in seen
                    and not any(ext in full_url for ext in ['.pdf', '.png', '.jpg', '.svg', '.css', '.js'])
                    and any(kw in full_url.lower() for kw in SUBPAGE_KEYWORDS)):

                    seen.add(full_url)
                    relevant_urls.append(full_url)

            return relevant_urls[:self.max_subpages + 2]  # Small buffer
        except Exception:
            return []

    def _extract_clean_content(self, page) -> str:
        """
        Extract clean text from page. Strips scripts, styles, nav, footer.
        Returns markdown for token efficiency.
        """
        try:
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg", "nav", "footer", "header"]):
                tag.decompose()

            # Remove elements with common boilerplate classes
            for element in soup.find_all(class_=re.compile(r"(cookie|banner|popup|modal|sidebar|menu|nav)", re.I)):
                element.decompose()

            # Convert to markdown (cleaner than raw text for LLM)
            markdown_content = md(str(soup), heading_style="ATX", strip=["img"])

            # Clean up excessive whitespace
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content).strip()

            # Token safety: cap at 3000 chars per page
            if len(markdown_content) > 3000:
                markdown_content = markdown_content[:3000] + "\n... [content truncated]"

            return markdown_content

        except Exception as e:
            logger.warning(f"   ⚠️ Content extraction failed: {str(e)}")
            return ""

    def _dismiss_overlays(self, page):
        """Try to dismiss cookie banners and popups."""
        overlay_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Accept All')",
            "button:has-text('Got it')",
            "button:has-text('Close')",
            "[data-testid='cookie-banner'] button",
            ".cookie-consent button",
        ]
        for selector in overlay_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click(timeout=1000)
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue  # No overlay found, that's fine