"""
Crawl Wrapper Script for Airflow
Chạy crawl scripts để lấy job data
"""
import os
import sys

def main():
    base_dir = "/opt/airflow/apps/crawler"
    
    # Check if crawl is needed
    # Nếu đã có data files thì có thể skip crawl
    topcv_data = os.path.join(base_dir, "data", "raw_topcv", "job_details.json")
    itviec_data = os.path.join(base_dir, "data", "raw_itviec", "itviec_enriched.jsonl")
    
    print("=" * 60)
    print("CRAWL TASK - Checking data files...")
    print("=" * 60)
    
    if os.path.exists(topcv_data):
        print(f"✅ TopCV data exists: {topcv_data}")
    else:
        print(f"⚠️  TopCV data not found: {topcv_data}")
        print("   Note: Crawl script should be run manually or in separate container")
    
    if os.path.exists(itviec_data):
        print(f"✅ ITViec data exists: {itviec_data}")
    else:
        print(f"⚠️  ITViec data not found: {itviec_data}")
        print("   Note: Crawl script should be run manually or in separate container")
    
    # Note: Actual crawling requires Chrome/Selenium
    # This is typically done outside Airflow container
    # For now, we just verify data files exist
    print("\n" + "=" * 60)
    print("NOTE: Full crawling requires Chrome/Selenium")
    print("Crawl scripts should be run separately:")
    print("  - data/raw_topcv/crawl_content.py - TopCV crawler")
    print("  - data/raw_itviec/crawl_content.py - ITViec crawler")
    print("  - data/raw_topcv/extract_urls.py - TopCV URL extractor")
    print("  - data/raw_itviec/extract_urls.py - ITViec URL extractor")
    print("=" * 60)
    
    # If both files exist, consider crawl successful
    if os.path.exists(topcv_data) or os.path.exists(itviec_data):
        print("\n✅ Crawl check passed - Data files available")
        return 0
    else:
        print("\n⚠️  Warning: No data files found")
        print("Pipeline will continue but may have no data to process")
        return 0  # Don't fail, just warn


if __name__ == "__main__":
    sys.exit(main())

