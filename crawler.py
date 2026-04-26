import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi,en;q=0.5",
        "Connection": "keep-alive",
    }
]

# Subpages to crawl for products/services
SUBPAGE_PATHS = [
    "/ca-nhan", "/personal", "/san-pham", "/products", "/services", "/dich-vu",
    "/vay-von", "/loans", "/vay", "/cho-vay",
    "/tiet-kiem", "/savings", "/gui-tiet-kiem",
    "/the", "/cards", "/the-tin-dung", "/the-ghi-no",
    "/ngan-hang-so", "/digital-banking", "/mobile-banking", "/internet-banking",
    "/khuyen-mai", "/promotions", "/uu-dai",
    "/dau-tu", "/investments", "/quy-dau-tu",
    "/bao-hiem", "/insurance",
    "/lai-suat", "/interest-rates", "/bieu-phi",
    "/doanh-nghiep", "/business", "/corporate",
    "/gioi-thieu", "/about",
]


def get_driver():
    """Khởi tạo Chrome headless driver với anti-detection"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--lang=vi-VN")
    options.add_argument("--disable-web-security")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['vi-VN', 'vi', 'en-US']});
        """
    })
    return driver


def crawl_with_requests(url):
    """Crawl bằng requests (không cần JS)"""
    for headers in HEADERS_LIST:
        try:
            session = requests.Session()
            session.headers.update(headers)
            resp = session.get(url, timeout=20, allow_redirects=True, verify=False)
            if resp.status_code == 200 and len(resp.text) > 500:
                print(f"✅ requests crawl OK: {len(resp.text)} chars")
                return resp.text
        except Exception as e:
            print(f"⚠️ requests attempt failed: {e}")
    return None


def get_root_url(url):
    """Lấy root domain từ URL"""
    parts = url.split("//")
    if len(parts) > 1:
        domain = parts[1].split("/")[0]
        return parts[0] + "//" + domain
    return url


def crawl_subpages(driver, root_url, max_pages=4):
    """Crawl các trang con quan trọng để lấy thêm dữ liệu sản phẩm"""
    extra_content = []
    tried = 0

    for path in SUBPAGE_PATHS:
        if tried >= max_pages:
            break
        sub_url = root_url.rstrip("/") + path
        try:
            driver.set_page_load_timeout(15)
            driver.get(sub_url)
            time.sleep(1.2)

            # Kiểm tra có redirect về 404 không
            current = driver.current_url
            if "404" in current or "error" in current.lower():
                continue

            soup = BeautifulSoup(driver.page_source, "html.parser")
            for tag in soup(["script", "style", "noscript", "iframe", "svg", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) > 400:
                extra_content.append(f"\n--- SUBPAGE [{path}]: {sub_url} ---\n{text[:2500]}")
                tried += 1
                print(f"  📄 Subpage {path}: {len(text)} chars")
        except Exception as e:
            pass

    return "\n".join(extra_content)


def extract_structured_data(soup):
    """Trích xuất dữ liệu có cấu trúc từ HTML"""
    data = {
        "products": [],
        "promotions": [],
        "digital": [],
        "rates": [],
        "nav_links": [],
        "headings": []
    }
    seen = set()

    # Headings
    for tag_name in ["h1", "h2", "h3"]:
        for elem in soup.find_all(tag_name)[:30]:
            t = elem.get_text(strip=True)
            if 4 < len(t) < 200 and t not in seen:
                data["headings"].append(t)
                seen.add(t)

    # Products từ các selector
    product_selectors = [
        "[class*='product']", "[class*='service']", "[class*='san-pham']",
        "[class*='dich-vu']", "[class*='item']", "[class*='card']",
        "[class*='package']", "[class*='plan']", "[class*='category']"
    ]
    for selector in product_selectors:
        for elem in soup.select(selector)[:20]:
            t = elem.get_text(strip=True)
            if 6 < len(t) < 160 and t not in seen:
                data["products"].append(t)
                seen.add(t)

    # Promotions
    promo_selectors = [
        "[class*='promo']", "[class*='offer']", "[class*='khuyen-mai']",
        "[class*='uu-dai']", "[class*='campaign']", "[class*='banner']",
        "[class*='promotion']", "[class*='deal']", "[class*='sale']"
    ]
    for selector in promo_selectors:
        for elem in soup.select(selector)[:15]:
            t = elem.get_text(strip=True)
            if 15 < len(t) < 400:
                data["promotions"].append(t[:250])

    # Navigation links (quan trọng để hiểu cấu trúc sản phẩm)
    for a in soup.find_all("a", href=True)[:60]:
        t = a.get_text(strip=True)
        href = a.get("href", "")
        if 3 < len(t) < 80 and t not in seen:
            data["nav_links"].append(f"{t} ({href})")
            seen.add(t)

    # Digital keywords
    body_text = soup.get_text().lower()
    digital_keywords = [
        "mobile banking", "internet banking", "digital banking", "e-banking",
        "app", "chatbot", "qr code", "vnpay", "smartbanking", "digibank",
        "ipay", "momo", "zalopay", "ekyc", "open banking", "api", "fintech"
    ]
    data["digital"] = [kw for kw in digital_keywords if kw in body_text]

    # Lãi suất / giá cả
    rates_raw = re.findall(r'(\d+[,.]?\d*)\s*%', body_text)
    seen_rates = set()
    for r in rates_raw:
        try:
            val = float(r.replace(',', '.'))
            if 0.5 <= val <= 30.0 and r not in seen_rates:
                data["rates"].append(r + '%')
                seen_rates.add(r)
                if len(data["rates"]) >= 15:
                    break
        except:
            pass

    return data


def crawl_website(url, max_retries=2):
    """
    Crawl website thực tế - Selenium ưu tiên, requests fallback.
    KHÔNG dùng knowledge base hay mock data.
    Trả về None nếu thực sự không crawl được.
    """
    driver = None
    root_url = get_root_url(url)

    # === CHIẾN LƯỢC 1: Selenium (có JS rendering) ===
    for attempt in range(max_retries):
        try:
            print(f"🌐 [Selenium] Crawling {url} (attempt {attempt+1}/{max_retries})...")
            driver = get_driver()
            driver.set_page_load_timeout(35)
            driver.get(url)

            # Đợi body load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2.5)

            # Scroll để trigger lazy load
            for frac in [0.25, 0.5, 0.75, 1.0]:
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {frac});")
                time.sleep(0.6)

            page_source = driver.page_source
            title = driver.title
            current_url = driver.current_url

            soup = BeautifulSoup(page_source, "html.parser")
            for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
                tag.decompose()

            structured = extract_structured_data(soup)
            main_text = soup.get_text(separator=" ", strip=True)
            main_text = re.sub(r'\s+', ' ', main_text).strip()

            if len(main_text) < 300:
                raise Exception(f"Content quá ngắn ({len(main_text)} chars) - bị block hoặc redirect")

            # Crawl subpages để lấy thêm chi tiết sản phẩm
            print(f"  🔍 Crawling subpages of {root_url}...")
            extra = crawl_subpages(driver, root_url, max_pages=4)

            result = f"""SOURCE: live_crawl
TITLE: {title}
URL: {url}
FINAL_URL: {current_url}

=== HEADINGS ===
{chr(10).join(structured['headings'][:30])}

=== PRODUCTS/SERVICES DETECTED ===
{' | '.join(structured['products'][:30])}

=== PROMOTIONS ===
{' | '.join(structured['promotions'][:12])}

=== DIGITAL FEATURES ===
{' | '.join(structured['digital'])}

=== RATES/PRICES ===
{' | '.join(structured['rates'])}

=== NAVIGATION ===
{' | '.join(structured['nav_links'][:25])}

=== MAIN PAGE CONTENT ===
{main_text[:5500]}

=== SUBPAGES CONTENT ===
{extra[:3500]}"""

            print(f"✅ Selenium OK: {len(result)} chars total")
            return result[:11000]

        except Exception as e:
            print(f"⚠️ Selenium attempt {attempt+1} failed: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(4)
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

    # === CHIẾN LƯỢC 2: requests (không JS) ===
    print(f"🔄 [requests] Trying {url}...")
    html = crawl_with_requests(url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
            tag.decompose()

        structured = extract_structured_data(soup)
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) >= 200:
            title_tag = soup.find("title")
            title = title_tag.get_text() if title_tag else url

            result = f"""SOURCE: live_crawl_requests
TITLE: {title}
URL: {url}

=== HEADINGS ===
{chr(10).join(structured['headings'][:25])}

=== PRODUCTS/SERVICES DETECTED ===
{' | '.join(structured['products'][:25])}

=== PROMOTIONS ===
{' | '.join(structured['promotions'][:10])}

=== DIGITAL FEATURES ===
{' | '.join(structured['digital'])}

=== RATES/PRICES ===
{' | '.join(structured['rates'])}

=== MAIN CONTENT ===
{text[:6000]}"""

            print(f"✅ requests OK: {len(result)} chars")
            return result[:10000]

    # === THỰC SỰ KHÔNG CRAWL ĐƯỢC ===
    print(f"❌ Cannot crawl {url} - all strategies failed")
    return None
