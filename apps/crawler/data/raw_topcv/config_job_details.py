STANDARD = {
    "SINGLE_FIELDS": {
        "job_title": "//h1[contains(@class, 'job-detail__info--title')]",
        # Header Info (Neo vào ID header-job-info)
        "salary": "//div[@id='header-job-info']//div[contains(@class,'job-detail__info--sections')]/div[contains(@class,'job-detail__info--section')][1]//div[contains(@class,'job-detail__info--section-content-value')]",
        "province": "//div[@id='header-job-info']//div[contains(@class,'job-detail__info--sections')]/div[contains(@class,'job-detail__info--section')][2]//div[contains(@class,'job-detail__info--section-content-value')]",
        "experience_years": "//div[@id='header-job-info']//div[contains(@class,'job-detail__info--sections')]/div[contains(@class,'job-detail__info--section')][3]//div[contains(@class,'job-detail__info--section-content-value')]",
        "deadline": "//div[contains(@class,'job-detail__info--deadline-date')]",
        
        # Main Content
        "job_description": "//div[contains(@class,'job-description__item')]//h3[contains(text(),'Mô tả công việc')]/following-sibling::div",
        "job_requirements": "//div[contains(@class,'job-description__item')]//h3[contains(text(),'Yêu cầu ứng viên')]/following-sibling::div",
        "job_benefits": "//div[contains(@class,'job-description__item')]//h3[contains(text(),'Quyền lợi')]/following-sibling::div",
        "job_location_detail": "//div[contains(@class,'job-description__item')]//h3[contains(text(),'Địa điểm làm việc')]/following-sibling::div",
        "working_time": "//div[contains(@class,'job-description__item')]//h3[contains(text(),'Thời gian làm việc')]/following-sibling::div",

        # Company Info
        "company_name": "//div[contains(@class,'company-name-label')]//a",
        "company_scale": "//div[contains(@class,'company-scale')]//div[@class='company-value']",
        "company_industry": "//div[contains(@class,'company-field')]//div[@class='company-value']",
        "company_address": "//div[contains(@class,'company-address')]//div[@class='company-value']",
        
        # General Info
        "job_level": "//div[contains(@class,'box-general-group-info-title') and contains(text(),'Cấp bậc')]/following-sibling::div",
        "academic_level": "//div[contains(@class,'box-general-group-info-title') and contains(text(),'Học vấn')]/following-sibling::div",
        "job_type": "//div[contains(@class,'box-general-group-info-title') and contains(text(),'Hình thức làm việc')]/following-sibling::div",
        "quantity": "//div[contains(@class,'box-general-group-info-title') and contains(text(),'Số lượng tuyển')]/following-sibling::div",
    },
    "LIST_FIELDS": {
        "tags_role": "//div[contains(@class,'box-category')]//div[contains(text(),'Danh mục Nghề liên quan')]/following-sibling::div//a",
        "tags_skill": "//div[contains(@class,'box-category')]//div[contains(text(),'Kỹ năng cần có')]/following-sibling::div//a | //div[contains(@class,'box-category')]//div[contains(text(),'Kỹ năng cần có')]/following-sibling::div//span",
        "tags_location": "//div[contains(@class,'box-category')]//div[contains(text(),'Khu vực')]/following-sibling::div//a | //div[contains(@class,'box-category')]//div[contains(text(),'Khu vực')]/following-sibling::div//span[contains(@class, 'box-category-tag')]",
    },
    "ATTRIBUTE_FIELDS": {
        "company_url": ("//div[contains(@class,'company-name-label')]//a", "href"),
    }
}
