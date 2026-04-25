import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def get_driver():
    """Khởi tạo Chrome headless driver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    # Ẩn dấu hiệu automation
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def crawl_website(url, max_retries=2):
    """Crawl website thật bằng Selenium Chromium - không dùng fallback"""
    driver = None

    for attempt in range(max_retries):
        try:
            print(f"🌐 Selenium crawling {url} (attempt {attempt + 1})...")
            driver = get_driver()
            driver.set_page_load_timeout(30)
            driver.get(url)

            # Đợi body load xong
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Scroll để trigger lazy load content
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(1)

            page_source = driver.page_source
            title = driver.title

            soup = BeautifulSoup(page_source, "html.parser")

            # Xóa noise
            for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
                tag.decompose()

            structured = extract_structured_data(soup)
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) < 300:
                raise Exception(f"Content quá ngắn ({len(text)} chars)")

            full_text = f"""TITLE: {title}
URL: {url}
PRODUCTS_FOUND: {' | '.join(structured['products'][:20])}
PROMOTIONS_FOUND: {' | '.join(structured['promotions'][:10])}
DIGITAL_FOUND: {' | '.join(structured['digital'])}
RATES_FOUND: {' | '.join(structured['rates'])}
CONTENT: {text[:7500]}"""

            print(f"✅ Crawled {len(full_text)} chars from {url}")
            return full_text[:9500]

        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed for {url}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(3)
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

    print(f"❌ Failed to crawl {url} after {max_retries} attempts")
    return None


def extract_structured_data(soup):
    """Trích xuất dữ liệu có cấu trúc từ HTML đã render"""
    data = {"products": [], "promotions": [], "digital": [], "rates": []}
    seen_products = set()

    try:
        product_selectors = [
            "[class*='product']", "[class*='service']",
            "[class*='san-pham']", "[class*='dich-vu']",
            ".product-card", ".service-item",
            "h2", "h3", "h4",
            "[class*='item']", "[class*='card']"
        ]
        for selector in product_selectors:
            for elem in soup.select(selector)[:25]:
                try:
                    text = elem.get_text(strip=True)
                    if 8 < len(text) < 150 and text not in seen_products:
                        data["products"].append(text)
                        seen_products.add(text)
                except:
                    pass

        promo_selectors = [
            "[class*='promo']", "[class*='offer']",
            "[class*='khuyen-mai']", "[class*='uu-dai']",
            "[class*='campaign']", "[class*='banner']",
            "[class*='promotion']"
        ]
        for selector in promo_selectors:
            for elem in soup.select(selector)[:12]:
                text = elem.get_text(strip=True)
                if 15 < len(text) < 300:
                    data["promotions"].append(text[:200])

        body_text = soup.get_text().lower()
        digital_keywords = [
            "app", "mobile banking", "internet banking", "digital banking",
            "e-banking", "chatbot", "qr code", "vnpay", "smartbanking",
            "digibank", "ipay", "momo", "zalopay"
        ]
        data["digital"] = [kw for kw in digital_keywords if kw in body_text]

        rates_raw = re.findall(r'(\d+[,.]?\d*)\s*%', body_text)
        seen_rates = set()
        valid_rates = []
        for r in rates_raw:
            val = float(r.replace(',', '.'))
            if 1.0 <= val <= 25.0 and r not in seen_rates:
                valid_rates.append(r + '%')
                seen_rates.add(r)
        data["rates"] = valid_rates[:10]

    except Exception as e:
        print(f"⚠️ extract_structured_data error: {e}")

    return data
