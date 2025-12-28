"""
Script to extract job URLs from TopCV website.
Run locally for easier debugging with Selenium.
"""

import time
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """Create and configure Chrome driver."""
    options = Options()
    
    if headless:
        options.add_argument('--headless=new')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Giảm khả năng bị phát hiện là bot
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent giống browser thật
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Ẩn webdriver property
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver


def debug_page(driver: webdriver.Chrome, url: str) -> None:
    """Debug a single page to see what's happening."""
    print(f"\n{'='*60}")
    print(f"DEBUG: Loading {url}")
    print('='*60)
    
    driver.get(url)
    time.sleep(3)
    
    print(f"\n📄 Title: {driver.title}")
    print(f"🔗 Current URL: {driver.current_url}")
    
    # Check if blocked by Cloudflare
    if "Cloudflare" in driver.title or "Attention Required" in driver.title:
        print("⚠️  BLOCKED BY CLOUDFLARE!")
        return
    
    # Try different selectors
    selectors_to_try = [
        ('CSS: .job-item-search-result', '.job-item-search-result'),
        ('CSS: .job-item', '.job-item'),
        ('CSS: a[href*="/viec-lam/"]', 'a[href*="/viec-lam/"]'),
        ('XPATH: box-header avatar', '//div[contains(@class, "box-header")]//div[contains(@class, "avatar")]//a'),
        ('CSS: .box-info-job', '.box-info-job'),
    ]
    
    print("\n🔍 Trying different selectors:")
    for name, selector in selectors_to_try:
        try:
            if 'XPATH' in name:
                elements = driver.find_elements(By.XPATH, selector)
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"  {name}: Found {len(elements)} elements")
        except Exception as e:
            print(f"  {name}: Error - {e}")
    
    # Find all job links
    print("\n📋 Job links found:")
    all_links = driver.find_elements(By.TAG_NAME, 'a')
    job_links = []
    for link in all_links:
        href = link.get_attribute('href')
        if href and '/viec-lam/' in href and href not in job_links:
            job_links.append(href)
    
    for i, link in enumerate(job_links[:10], 1):
        print(f"  {i}. {link}")
    
    if len(job_links) > 10:
        print(f"  ... and {len(job_links) - 10} more links")
    
    # Save screenshot for visual debug
    screenshot_path = Path(__file__).parent / "debug_screenshot.png"
    driver.save_screenshot(str(screenshot_path))
    print(f"\n📸 Screenshot saved to: {screenshot_path}")


def extract_job_urls(driver: webdriver.Chrome, page_count: int = 38) -> list[str]:
    """Extract all job URLs from TopCV."""
    all_job_urls = []
    
    for page in range(1, page_count + 1):
        url = f"https://www.topcv.vn/viec-lam-it?page={page}"
        print(f"\n[{page}/{page_count}] Loading: {url}")
        
        driver.get(url)
        time.sleep(2)  # Đợi page load
        
        try:
            # Đợi content load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/viec-lam/"]'))
            )
            
            # Lấy tất cả job links
            all_links = driver.find_elements(By.TAG_NAME, 'a')
            page_jobs = []
            
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/viec-lam/' in href and '/viec-lam-it' not in href:
                    if href not in page_jobs and href not in all_job_urls:
                        page_jobs.append(href)
            
            all_job_urls.extend(page_jobs)
            print(f"  ✓ Found {len(page_jobs)} jobs (Total: {len(all_job_urls)})")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Delay giữa các request
        time.sleep(1)
    
    return all_job_urls


def save_urls(urls: list[str], output_file: str = "job_urls.json") -> None:
    """Save URLs to JSON file."""
    output_path = Path(__file__).parent / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(urls)} URLs to: {output_path}")


def main():
    """Main function."""
    print("🚀 TopCV URL Extractor")
    print("="*60)
    
    driver = None
    
    try:
        # Chạy KHÔNG headless để debug
        driver = create_driver(headless=False)
        
        # Debug 1 trang trước
        debug_page(driver, "https://www.topcv.vn/viec-lam-it?page=1")
        
        # Hỏi user có muốn tiếp tục không
        input("\n⏸️  Press Enter to continue extracting all pages (or Ctrl+C to stop)...")
        
        # Extract tất cả pages
        urls = extract_job_urls(driver, page_count=38)
        
        # Save kết quả
        if urls:
            save_urls(urls)
        else:
            print("\n❌ No URLs extracted!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            print("\n🔒 Driver closed")


if __name__ == "__main__":
    main()
