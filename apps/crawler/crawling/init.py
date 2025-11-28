from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time


def init_crawl_single_url(url):
    # Initialize Selenium config
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    results = []

    try:
        print(f"Đang truy cập: {url}")
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        script = driver.find_element(
            By.CSS_SELECTOR, "script[type='application/ld+json']"
        )
        data = json.loads(script.get_attribute("innerHTML"))

        results = [
            item.get("url")
            for item in data.get("itemListElement", [])
            if item.get("url")
        ]

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return results


if __name__ == "__main__":
    all_urls = []

    with open("../data/urls.txt", "r", encoding="utf-8") as f:
        urls = [
            line.strip(""""' ,\r\n""")
            for line in f
            if line.strip() and line.strip().startswith("http")
        ]

    for url in urls:
        job_urls = init_crawl_single_url(url)
        all_urls.extend(job_urls)
        time.sleep(1)

    with open("../data/job_urls.txt", "w", encoding="utf-8") as f:
        for url in all_urls:
            f.write(url + "\n")
