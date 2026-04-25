import requests
from bs4 import BeautifulSoup
import time
import re
import json

def crawl_website(url, max_retries=2):
    """Crawl website với trích xuất dữ liệu có cấu trúc"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9",
    }
    
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=20, verify=False)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Xóa noise
            for tag in soup(["script", "style", "nav", "footer", "form", "iframe"]):
                tag.decompose()
            
            # Trích xuất dữ liệu
            structured = extract_structured_data(soup)
            
            # Lấy text
            text = soup.get_text(separator=" ", strip=True)
            
            # Kết hợp
            full_text = f"""
TITLE: {soup.title.get_text(strip=True) if soup.title else ''}
PRODUCTS: {structured['products']}
PROMOTIONS: {structured['promotions']}
DIGITAL: {structured['digital']}
RATES: {structured['rates']}
CONTENT: {text[:7000]}
"""
            return full_text[:9000]
            
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    return None

def extract_structured_data(soup):
    """Trích xuất dữ liệu có cấu trúc"""
    data = {
        "products": [],
        "promotions": [],
        "digital": [],
        "rates": []
    }
    
    try:
        # Tìm sản phẩm
        for selector in ["[class*='product']", "[class*='service']", ".product-card", ".service-item", "h2", "h3"]:
            for elem in soup.select(selector)[:20]:
                try:
                    text = elem.get_text(strip=True)
                    if 10 < len(text) < 200 and text not in data["products"]:
                        data["products"].append(text)
                except:
                    pass
        
        # Tìm khuyến mãi
        for selector in ["[class*='promo']", "[class*='offer']", "[class*='campaign']"]:
            for elem in soup.select(selector)[:10]:
                text = elem.get_text(strip=True)
                if 15 < len(text) < 300:
                    data["promotions"].append(text[:150])
        
        # Tìm dịch vụ digital
        body_text = soup.get_text().lower()
        digital_keywords = ["app", "mobile", "online", "digital", "internet banking", "e-banking", "chatbot"]
        data["digital"] = [kw for kw in digital_keywords if kw in body_text]
        
        # Tìm lãi suất
        rates = re.findall(r'(\d+\.?\d*)\s*%', body_text)
        data["rates"] = sorted(list(set(rates)))[:5]
        
    except Exception as e:
        print(f"Error extracting: {e}")
    
    return data
