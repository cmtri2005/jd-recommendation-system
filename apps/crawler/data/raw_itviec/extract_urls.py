import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os
import random


def get_jobs_from_current_page(driver, url):
    results = []
    try:
        print(f"    -> Đang đọc: {url}")
        driver.get(url)

        time.sleep(random.uniform(3, 6))

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.job-body, div.job-card, h3")
                )
            )
        except:
            print("[!] Web load chậm hoặc đang verify. Đợi thêm chút...")
            time.sleep(5)

        try:
            script = driver.find_element(
                By.CSS_SELECTOR, "script[type='application/ld+json']"
            )
            data = json.loads(script.get_attribute("innerHTML"))

            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "ItemList":
                        results = [
                            e.get("url")
                            for e in item.get("itemListElement", [])
                            if e.get("url")
                        ]
            elif isinstance(data, dict):
                results = [
                    item.get("url")
                    for item in data.get("itemListElement", [])
                    if item.get("url")
                ]
        except:
            pass

        if len(results) == 0:
            try:

                job_elements = driver.find_elements(
                    By.CSS_SELECTOR, "h3 a[href*='/it-jobs/']"
                )

                if not job_elements:
                    job_elements = driver.find_elements(
                        By.CSS_SELECTOR, "a[class*='job'][href*='/it-jobs/']"
                    )

                for elem in job_elements:
                    link = elem.get_attribute("href")

                    if (
                        link
                        and "/it-jobs/" in link
                        and "jobs-expertise" not in link
                        and link not in results
                    ):
                        results.append(link)
            except:
                pass

    except Exception as e:
        print(f"    [!] Lỗi tải trang: {e}")
        return []

    return results


def crawl_category_pagination(category_url):
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")

    driver = uc.Chrome(options=options, use_subprocess=True)

    collected_jobs = set()
    page = 1
    max_pages = 50

    print(f"Bắt đầu quét Category: {category_url}")

    try:
        while page <= max_pages:
            if page == 1:
                target_url = category_url
            else:
                connector = "&" if "?" in category_url else "?"
                target_url = f"{category_url}{connector}page={page}"

            jobs_on_page = get_jobs_from_current_page(driver, target_url)

            if not jobs_on_page:
                print(
                    f"Không tìm thấy job nào ở trang {page}. (Có thể hết trang hoặc bị chặn cứng). Dừng."
                )
                break

            initial_count = len(collected_jobs)
            collected_jobs.update(jobs_on_page)
            new_count = len(collected_jobs)

            print(
                f"    + Trang {page}: Tìm thấy {len(jobs_on_page)} jobs. (Tổng tích lũy: {new_count})"
            )

            if page > 1 and new_count == initial_count:
                print("    [!] Dữ liệu không tăng thêm. Có thể đã hết trang. Dừng.")
                break

            page += 1

            time.sleep(random.uniform(2, 4))

    finally:
        driver.quit()

    return list(collected_jobs)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "urls.txt")
    output_path = os.path.join(base_dir, "job_urls.txt")

    final_unique_urls = set()

    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip().startswith("http")]

        for url in urls:
            job_urls = crawl_category_pagination(url)
            final_unique_urls.update(job_urls)
            print(f"Xong category này. Tổng job hiện tại: {len(final_unique_urls)}\n")

            time.sleep(5)

        with open(output_path, "w", encoding="utf-8") as f:
            for url in final_unique_urls:
                f.write(url + "\n")

        print(
            f"[HOÀN TẤT] Đã lưu {len(final_unique_urls)} job unique vào {output_path}"
        )
    else:
        print(f"Không tìm thấy file: {input_path}")
