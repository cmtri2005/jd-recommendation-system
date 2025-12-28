"""
Script to crawl job details from TopCV URLs.
Uses schema from config_job_details.py to extract structured data.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


from data.raw_topcv.config_job_details import STANDARD

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TopCVCrawler:
    """Crawler for TopCV job details."""

    def __init__(self, headless: bool = True, delay: float = 2.0):
        """
        Initialize the crawler.

        Args:
            headless: Run browser in headless mode
            delay: Delay between requests in seconds
        """
        self.headless = headless
        self.delay = delay
        self.driver = None
        self.schema = STANDARD

    def create_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome driver."""
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # Anti-detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Hide webdriver property
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
            },
        )

        return driver

    def start(self):
        """Start the crawler."""
        self.driver = self.create_driver()
        logger.info("Browser started successfully")

    def stop(self):
        """Stop the crawler and close browser."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")

    def extract_single_field(self, xpath: str) -> str | None:
        """Extract text from a single element using XPath."""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip() if element.text else None
        except Exception:
            return None

    def extract_list_field(self, xpath: str) -> list[str]:
        """Extract text from multiple elements using XPath."""
        try:
            elements = self.driver.find_elements(By.XPATH, xpath)
            return [el.text.strip() for el in elements if el.text.strip()]
        except Exception:
            return []

    def extract_attribute_field(self, xpath: str, attribute: str) -> str | None:
        """Extract attribute value from an element using XPath."""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.get_attribute(attribute)
        except Exception:
            return None

    def crawl_job(self, url: str) -> dict[str, Any]:
        """
        Crawl a single job page and extract data.

        Args:
            url: Job page URL

        Returns:
            Dictionary of extracted job data
        """
        job_data = {
            "url": url,
            "crawled_at": datetime.now().isoformat(),
        }

        try:
            # Navigate to page
            self.driver.get(url)
            time.sleep(self.delay)

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Check if blocked by Cloudflare
            if (
                "Cloudflare" in self.driver.title
                or "Attention Required" in self.driver.title
            ):
                logger.warning(f"Blocked by Cloudflare: {url}")
                job_data["error"] = "blocked_by_cloudflare"
                return job_data

            # Extract SINGLE_FIELDS
            for field_name, xpath in self.schema.get("SINGLE_FIELDS", {}).items():
                job_data[field_name] = self.extract_single_field(xpath)

            # Extract LIST_FIELDS
            for field_name, xpath in self.schema.get("LIST_FIELDS", {}).items():
                job_data[field_name] = self.extract_list_field(xpath)

            # Extract ATTRIBUTE_FIELDS
            for field_name, (xpath, attr) in self.schema.get(
                "ATTRIBUTE_FIELDS", {}
            ).items():
                job_data[field_name] = self.extract_attribute_field(xpath, attr)

            job_data["success"] = True

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            job_data["error"] = str(e)
            job_data["success"] = False

        return job_data

    def crawl_jobs(
        self,
        urls: list[str],
        output_file: str = "job_details.json",
        save_interval: int = 10,
    ) -> list[dict]:
        """
        Crawl multiple job pages.

        Args:
            urls: List of job URLs to crawl
            output_file: Output file path
            save_interval: Save results every N jobs

        Returns:
            List of crawled job data
        """
        results = []
        output_path = Path(__file__).parent / output_file

        # Load existing results if any
        if output_path.exists():
            with open(output_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
                results = existing.get("jobs", [])
                crawled_urls = {job["url"] for job in results}
                urls = [url for url in urls if url not in crawled_urls]
                logger.info(
                    f"Loaded {len(results)} existing jobs, {len(urls)} remaining"
                )

        total = len(urls)
        success_count = 0

        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{total}] Crawling: {url}")

            job_data = self.crawl_job(url)
            results.append(job_data)

            if job_data.get("success"):
                success_count += 1

            # Save periodically
            if i % save_interval == 0:
                self._save_results(results, output_path)
                logger.info(f"Saved progress: {len(results)} jobs")

            # Add delay between requests
            if i < total:
                time.sleep(self.delay)

        # Final save
        self._save_results(results, output_path)

        logger.info(f"\n{'='*60}")
        logger.info(f"Crawling completed!")
        logger.info(f"Total: {len(results)} jobs")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failed: {len(results) - success_count}")
        logger.info(f"Saved to: {output_path}")

        return results

    def _save_results(self, results: list[dict], output_path: Path):
        """Save results to JSON file."""
        output_data = {
            "metadata": {
                "crawled_at": datetime.now().isoformat(),
                "total_jobs": len(results),
                "success_count": sum(1 for r in results if r.get("success")),
            },
            "jobs": results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)


def load_urls(file_path: str = "job_urls.json") -> list[str]:
    """Load job URLs from JSON file."""
    path = Path(__file__).parent / file_path

    with open(path, "r", encoding="utf-8") as f:
        urls = json.load(f)

    logger.info(f"Loaded {len(urls)} URLs from {path}")
    return urls


def main():
    """Main function."""
    print("🚀 TopCV Job Details Crawler")
    print("=" * 60)

    # Load URLs
    urls = load_urls("job_urls.json")

    # Limit for testing (remove or increase in production)
    # urls = urls[:5]  # Uncomment to test with first 5 URLs

    crawler = TopCVCrawler(headless=False, delay=2.0)

    try:
        crawler.start()

        # Debug first URL
        if urls:
            print(f"\n📋 Testing first URL: {urls[0]}")
            job = crawler.crawl_job(urls[0])

            print("\n✅ Extracted fields:")
            for key, value in job.items():
                if value and key not in ["url", "crawled_at", "success"]:
                    if isinstance(value, list):
                        print(
                            f"  {key}: {value[:3]}..."
                            if len(value) > 3
                            else f"  {key}: {value}"
                        )
                    else:
                        display = (
                            str(value)[:100] + "..." if len(str(value)) > 100 else value
                        )
                        print(f"  {key}: {display}")

            # Ask to continue
            user_input = input("\n⏸️  Press Enter to crawl all URLs (or 'q' to quit): ")
            if user_input.lower() == "q":
                print("Stopped by user")
                return

        # Crawl all URLs
        crawler.crawl_jobs(urls, output_file="job_details.json", save_interval=10)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        crawler.stop()


if __name__ == "__main__":
    main()
