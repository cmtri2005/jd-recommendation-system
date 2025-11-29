import json
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contextlib import closing

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def get_section_content(driver, header_keyword):
    try:
        xpath = f"//div[contains(@class, 'paragraph') and .//h2[contains(text(), '{header_keyword}')]]"
        element = driver.find_element(By.XPATH, xpath)
        
        raw_text = element.text
        
        clean_text = raw_text.replace(header_keyword, "").strip()
        return clean_text
    except Exception:
        return ""

def crawl_data(url: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3") 

    with closing(webdriver.Chrome(options=options)) as driver:
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        try:
            type_job = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text.strip()
        except:
            type_job = "Unknown"

        try:
            time_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Posted') and contains(@class, 'text-rich-grey')]")
            time_posted = time_element.text.strip() # Kết quả sẽ là "Posted 1 day ago"
        except:
            time_posted = "Unknown"

        required_skills = []
        try:
            
            skills_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'igap-2')]//a")
            required_skills = [e.text.strip() for e in skills_elements]
        except:
            pass

        job_description = get_section_content(driver, "Job description")

        your_skills_exp = get_section_content(driver, "Your skills and experience")

        
        if not job_description and not your_skills_exp:
             try:
                paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.paragraph")
                if len(paragraphs) >= 1:
                    job_description = paragraphs[0].text
                if len(paragraphs) >= 2:
                    your_skills_exp = paragraphs[1].text
             except: pass

        result = {
            "url": url,
            "job_title": type_job,
            "required_skills": required_skills,
            "time_posted_raw": time_posted,
            "job_description": job_description,
            "your_skills_experience": your_skills_exp
        }

        return result

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "..", "data", "job_urls.txt")
    output_path = os.path.join(base_dir, "..", "data", "jobs_raw.jsonl")

    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Bắt đầu crawl {len(urls)} jobs. Lưu tại: {output_path}")
        
        with open(output_path, "a", encoding="utf-8") as f_out:
            for i, url in enumerate(urls):
                try:
                    data = crawl_data(url)
                    
                    # Log kiểm tra
                    skills_count = len(data['required_skills'])
                    desc_preview = data['job_description'][:30].replace("\n", " ")
                    logging.info(f"[{i+1}/{len(urls)}] OK: {data['job_title']} | Skills: {skills_count} | Time: {data['time_posted_raw']}")
                    
                    f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
                    f_out.flush() 
                    
                except Exception as e:
                    logging.error(f"Lỗi {url}: {e}")

                # time.sleep(1) 
                
        print("Hoàn tất.")
    else:
        print("Không tìm thấy file input.")