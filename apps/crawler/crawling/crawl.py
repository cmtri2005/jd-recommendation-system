import json
import re
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.insert_table import insert_table
from contextlib import closing


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_time_posted(text: str) -> datetime:
    now = datetime.now()
    if m := re.search(r"(\d+)\s+days?", text):
        return now - timedelta(days=int(m.group(1)))
    elif m := re.search(r"(\d+)\s+hours?", text):
        return now - timedelta(hours=int(m.group(1)))
    elif m := re.search(r"(\d+)\s+minutes?", text):
        return now - timedelta(minutes=int(m.group(1)))
    elif m := re.search(r"(\d+)\s+seconds?", text):
        return now - timedelta(seconds=int(m.group(1)))
    return now


def crawl_data(url: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    with closing(webdriver.Chrome(options=options)) as driver:
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        try:
            type_job = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.text-reset.itag[title]"))
            ).text.strip()
        except Exception as e:
            logging.warning(f"Not found type job element: {e}")
            type_job = None

        try:
            time_text = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.preview-header-item svg + span.normal-text.text-rich-grey")
                )
            ).text.strip()
            time_posted = parse_time_posted(time_text)
        except Exception as e:
            logging.warning(f"Not found time posted element: {e}")
            time_posted = datetime.now()

        try:
            skills_elements = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.d-flex.flex-wrap.igap-2 a.text-reset.itag")
                )
            )
            required_skills = [e.text.strip() for e in skills_elements]
        except Exception as e:
            logging.warning(f"Not found skill elements: {e}")
            required_skills = []

        result = {
            "type_job": type_job,
            "required_skills": required_skills,
            "time_posted": time_posted,
            "url": url,
        }

        insert_table(type_job, required_skills, time_posted, url)
        return result


if __name__ == "__main__":
    with open("data/job_urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f]
    for url in urls:
        data = crawl_data(url)
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        time.sleep(1)
