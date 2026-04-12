import requests
from bs4 import BeautifulSoup
import time
import urllib3

# Tắt warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def crawl_with_retry(url, max_retries=3):
    """Crawl với retry và SSL handling"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    
    for attempt in range(max_retries):
        try:
            # Thử HTTPS trước, nếu lỗi SSL thì verify=False
            verify_ssl = (attempt == 0)  # Chỉ verify ở lần đầu
            
            res = requests.get(
                url, 
                headers=headers, 
                timeout=20, 
                allow_redirects=True,
                verify=verify_ssl
            )
            res.raise_for_status()
            
            # Parse với html.parser
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside", "iframe", "noscript"]):
                tag.decompose()
            
            # Extract nhiều content hơn
            title = soup.title.get_text(strip=True) if soup.title else ""
            
            # Meta
            meta_desc = ""
            meta = soup.find("meta", attrs={"name": "description"})
            if meta:
                meta_desc = meta.get("content", "")
            
            # Headings
            h1_list = [h.get_text(strip=True) for h in soup.find_all("h1")[:5]]
            h2_list = [h.get_text(strip=True) for h in soup.find_all("h2")[:10]]
            h3_list = [h.get_text(strip=True) for h in soup.find_all("h3")[:10]]
            
            # Tìm các section sản phẩm
            product_sections = []
            keywords = ["sản phẩm", "tiết kiệm", "cho vay", "thẻ", "bảo hiểm", "dịch vụ", "lãi suất", "khuyến mãi"]
            
            for elem in soup.find_all(["div", "section", "article", "main"]):
                text = elem.get_text(strip=True)
                if any(kw in text.lower() for kw in keywords) and 100 < len(text) < 1000:
                    product_sections.append(text[:800])
            
            # Body text
            body_text = soup.get_text(separator=" ", strip=True)
            
            full_text = f"""
TITLE: {title}
META: {meta_desc}
H1: {' | '.join(h1_list)}
H2: {' | '.join(h2_list)}
H3: {' | '.join(h3_list)}
PRODUCT_SECTIONS: {' | '.join(list(set(product_sections))[:8])}
CONTENT: {body_text[:6000]}
"""
            return full_text[:8000]
            
        except requests.exceptions.SSLError as e:
            print(f"      ⚠️ SSL Error (attempt {attempt+1}), retrying without verify...")
            time.sleep(1)
            continue
            
        except requests.exceptions.RequestException as e:
            print(f"      ⚠️ Request error (attempt {attempt+1}): {str(e)[:50]}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return f"ERROR_CRAWL: {url} | {str(e)}"
            
        except Exception as e:
            return f"ERROR_CRAWL: {url} | {str(e)}"
    
    return f"ERROR_CRAWL: {url} | Max retries exceeded"

def crawl_website(url):
    """Wrapper với delay"""
    time.sleep(0.5)  # Delay nhẹ giữa các request
    return crawl_with_retry(url)
