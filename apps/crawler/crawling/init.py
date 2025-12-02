from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

def init_crawl_single_url(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    driver = webdriver.Chrome(options=options)
    results = []

    try:
        print(f"--> Quét: {url}")
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1)

        # Lấy dữ liệu từ JSON-LD (Script ẩn chứa data cấu trúc)
        script = driver.find_element(
            By.CSS_SELECTOR, "script[type='application/ld+json']"
        )
        data = json.loads(script.get_attribute("innerHTML"))

        # Xử lý format JSON trả về để lấy URL
        if isinstance(data, list):
             for item in data:
                if item.get("@type") == "ItemList":
                     results = [e.get("url") for e in item.get("itemListElement", []) if e.get("url")]
        elif isinstance(data, dict):
            results = [
                item.get("url")
                for item in data.get("itemListElement", [])
                if item.get("url")
            ]

    except Exception as e:
        print(f"Lỗi {url}: {e}")
    finally:
        driver.quit()

    return results

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, "..", "data", "urls.txt")
    output_path = os.path.join(base_dir, "..", "data", "job_urls.txt")

    all_urls = []
    
    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip().startswith("http")]

        for url in urls:
            job_urls = init_crawl_single_url(url)
            print(f"   + Tìm thấy {len(job_urls)} jobs.")
            all_urls.extend(job_urls)
            time.sleep(1)

        with open(output_path, "w", encoding="utf-8") as f:
            for url in all_urls:
                f.write(url + "\n")
        print(f"Đã lưu tổng cộng {len(all_urls)} job link vào {output_path}")
    else:
        print(f"Không tìm thấy file: {input_path}")