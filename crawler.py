from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crawl_with_selenium(url, max_retries=2):
    """Crawl với Selenium để xử lý JavaScript"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    for attempt in range(max_retries):
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            logger.info(f"🌐 Loading {url}...")
            driver.get(url)
            
            # Chờ các phần tử quan trọng load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='product'], [class*='service'], [class*='offering']"))
                )
            except:
                logger.warning("⏱️ Timeout waiting for products, continuing anyway...")
            
            # Scroll để load lazy-loaded content
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(1)
            
            # Lấy HTML đầy đủ
            html = driver.page_source
            
            # Trích xuất dữ liệu có cấu trúc
            extracted_data = extract_structured_data(driver, url)
            
            return html, extracted_data
            
        except Exception as e:
            logger.error(f"❌ Selenium error (attempt {attempt+1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                return None, None
        finally:
            if driver:
                driver.quit()
    
    return None, None

def extract_structured_data(driver, url):
    """Trích xuất dữ liệu có cấu trúc từ trang"""
    data = {
        "products": [],
        "promotions": [],
        "digital_services": [],
        "interest_rates": {},
        "contact_info": {}
    }
    
    try:
        # Tìm sản phẩm
        product_selectors = [
            "[class*='product']", "[class*='service']", "[class*='offering']",
            "[data-product]", ".product-card", ".service-item"
        ]
        
        for selector in product_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:20]:  # Giới hạn 20 sản phẩm
                    try:
                        name = elem.find_element(By.CSS_SELECTOR, "h2, h3, .name, .title").text
                        description = elem.find_element(By.CSS_SELECTOR, "p, .description").text
                        if name and name not in [p["name"] for p in data["products"]]:
                            data["products"].append({
                                "name": name,
                                "description": description[:200],
                                "category": categorize_product(name)
                            })
                    except:
                        pass
            except:
                pass
        
        # Tìm khuyến mãi
        promo_selectors = [
            "[class*='promotion']", "[class*='offer']", "[class*='campaign']",
            ".promo-banner", ".offer-card"
        ]
        
        for selector in promo_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:10]:
                    try:
                        text = elem.text
                        if text and len(text) > 10:
                            data["promotions"].append(text[:150])
                    except:
                        pass
            except:
                pass
        
        # Tìm dịch vụ digital
        digital_keywords = ["app", "mobile", "online", "digital", "internet banking", "e-banking"]
        all_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        for keyword in digital_keywords:
            if keyword in all_text:
                data["digital_services"].append(keyword.title())
        
        # Tìm lãi suất
        rate_patterns = [
            r"(\d+\.?\d*)\s*%\s*(lãi|suất|rate)",
            r"lãi\s*suất\s*(\d+\.?\d*)\s*%"
        ]
        
        import re
        for pattern in rate_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches[:5]:
                if isinstance(match, tuple):
                    data["interest_rates"][f"rate_{len(data['interest_rates'])}"] = f"{match[0]}%"
                else:
                    data["interest_rates"][f"rate_{len(data['interest_rates'])}"] = f"{match}%"
        
    except Exception as e:
        logger.error(f"Error extracting structured data: {e}")
    
    return data

def categorize_product(name):
    """Phân loại sản phẩm"""
    name_lower = name.lower()
    
    categories = {
        "SAVINGS": ["tiết kiệm", "gửi", "deposit", "savings"],
        "LOAN": ["vay", "cho vay", "loan", "credit"],
        "CARD": ["thẻ", "card"],
        "DIGITAL": ["app", "mobile", "online", "digital"],
        "INSURANCE": ["bảo hiểm", "insurance"],
        "INVESTMENT": ["đầu tư", "investment", "chứng chỉ"],
    }
    
    for category, keywords in categories.items():
        if any(kw in name_lower for kw in keywords):
            return category
    
    return "OTHER"

def crawl_website(url):
    """Main crawl function"""
    html, structured = crawl_with_selenium(url)
    
    if not html:
        # Fallback to requests
        import requests
        from bs4 import BeautifulSoup
        try:
            res = requests.get(url, timeout=20, verify=False)
            html = res.text
            structured = None
        except:
            return None, None
    
    return html, structured
