import requests
from bs4 import BeautifulSoup
import time
import re
import random

HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
    }
]

# Known Vietnamese bank product data (fallback khi website block)
BANK_KNOWLEDGE = {
    "techcombank": {
        "full_name": "Techcombank (Ngân hàng TMCP Kỹ Thương Việt Nam)",
        "code": "TCB",
        "known_products": [
            "Tài khoản thanh toán Techcombank",
            "Tiết kiệm linh hoạt F@st i-Saving",
            "Tiết kiệm có kỳ hạn",
            "Vay mua nhà",
            "Vay ô tô",
            "Vay tín chấp cá nhân",
            "Thẻ Techcombank Visa Platinum",
            "Thẻ Techcombank Mastercard",
            "Techcombank ONE - App ngân hàng số",
            "Bảo hiểm nhân thọ Techcombank Life",
            "Quỹ mở Techcombank",
            "Dịch vụ ngoại hối",
        ],
        "digital": ["Techcombank ONE App", "Internet Banking", "SMS Banking", "VNPAY QR"],
        "promotions": [
            "Mở tài khoản trực tuyến nhận thưởng",
            "Hoàn tiền thẻ tín dụng lên đến 5%",
            "Lãi suất ưu đãi vay mua nhà"
        ],
        "rates": {"savings": "4.5% - 6.5%", "loan": "7.5% - 12%"},
        "positioning": "Ngân hàng tư nhân hàng đầu, định hướng số hóa, phục vụ khách hàng trung-cao cấp và doanh nghiệp vừa",
        "strengths": ["Hệ sinh thái số mạnh", "Dịch vụ Premium", "Mạng lưới doanh nghiệp lớn"],
        "weaknesses": ["Phí dịch vụ cao hơn ngân hàng quốc doanh", "Ít chi nhánh tại vùng nông thôn"]
    },
    "bidv": {
        "full_name": "BIDV (Ngân hàng TMCP Đầu tư và Phát triển Việt Nam)",
        "code": "BIDV",
        "known_products": [
            "Tài khoản thanh toán BIDV",
            "Tiết kiệm BIDV Online",
            "Tiết kiệm bậc thang",
            "Vay mua nhà ở xã hội",
            "Vay mua ô tô",
            "Vay sản xuất kinh doanh",
            "Thẻ BIDV Visa",
            "Thẻ BIDV Mastercard Infinite",
            "BIDV SmartBanking App",
            "Bảo hiểm MetLife - BIDV",
            "Trái phiếu BIDV",
            "Tín dụng xuất nhập khẩu",
        ],
        "digital": ["BIDV SmartBanking", "BIDV Online", "QR Pay", "BIDV Pay+"],
        "promotions": [
            "Gửi tiết kiệm online lãi suất cao hơn 0.2%",
            "Vay ưu đãi nhà ở xã hội 4.8%/năm",
            "Hoàn tiền 2% thẻ tín dụng quốc tế"
        ],
        "rates": {"savings": "3.8% - 6.1%", "loan": "6.5% - 11%"},
        "positioning": "Ngân hàng quốc doanh lớn, mạnh về tín dụng doanh nghiệp và bán lẻ, phủ sóng toàn quốc",
        "strengths": ["Mạng lưới chi nhánh rộng khắp", "Uy tín nhà nước", "Lãi suất vay ưu đãi"],
        "weaknesses": ["Chuyển đổi số chậm hơn ngân hàng tư nhân", "Thủ tục hành chính còn nhiều"]
    },
    "vietinbank": {
        "full_name": "VietinBank (Ngân hàng TMCP Công Thương Việt Nam)",
        "code": "CTG",
        "known_products": [
            "Tài khoản thanh toán VietinBank",
            "Tiết kiệm trực tuyến VietinBank",
            "Tiết kiệm linh hoạt",
            "Vay mua nhà",
            "Vay tiêu dùng",
            "Vay SME doanh nghiệp nhỏ",
            "Thẻ VietinBank Visa",
            "Thẻ VietinBank JCB",
            "VietinBank iPay App",
            "Bảo hiểm VBI",
            "Đầu tư chứng khoán VietinBank",
            "Dịch vụ thanh toán quốc tế SWIFT",
        ],
        "digital": ["VietinBank iPay", "Internet Banking", "QR Code", "VietinBank Pay"],
        "promotions": [
            "Tiết kiệm online lãi suất +0.3% so quầy",
            "Vay ưu đãi cán bộ nhân viên",
            "Phát hành thẻ miễn phí năm đầu"
        ],
        "rates": {"savings": "3.8% - 6.2%", "loan": "6.8% - 11.5%"},
        "positioning": "Ngân hàng thương mại nhà nước lớn thứ 2, mạnh về tín dụng công nghiệp và doanh nghiệp",
        "strengths": ["Nền tảng doanh nghiệp mạnh", "Hệ thống ATM rộng", "Thương hiệu lâu năm"],
        "weaknesses": ["App UX chưa cạnh tranh", "Lãi suất tiết kiệm thấp hơn tư nhân"]
    },
    "vietcombank": {
        "full_name": "Vietcombank (Ngân hàng TMCP Ngoại Thương Việt Nam)",
        "code": "VCB",
        "known_products": [
            "Tài khoản Vietcombank",
            "Tiết kiệm không kỳ hạn",
            "Tiết kiệm có kỳ hạn lãi cao",
            "Vay mua bất động sản",
            "Vay ô tô lãi suất thấp",
            "Vay tín chấp cá nhân",
            "Thẻ Vietcombank Visa Platinum",
            "Thẻ Vietcombank Mastercard World",
            "VCB Digibank App",
            "Bảo hiểm nhân thọ Vietcombank Cardif",
            "Quỹ đầu tư VCBF",
            "Thanh toán xuất nhập khẩu",
        ],
        "digital": ["VCB Digibank", "VCB Money", "QR Pay", "VCB Tokenization"],
        "promotions": [
            "Mở thẻ online hoàn tiền 10% tháng đầu",
            "Lãi suất tiết kiệm online cao nhất 6.8%",
            "Vay nhà lãi suất cố định 7.9% 2 năm"
        ],
        "rates": {"savings": "4.0% - 6.8%", "loan": "7.0% - 12%"},
        "positioning": "Ngân hàng ngoại thương lớn nhất, thương hiệu số 1 Việt Nam, mạnh về thanh toán quốc tế",
        "strengths": ["Thương hiệu mạnh nhất", "Dẫn đầu số hóa trong quốc doanh", "Mạng lưới quốc tế"],
        "weaknesses": ["Quy trình duyệt vay chậm", "Phí dịch vụ cao"]
    }
}


def get_bank_key(url):
    """Nhận diện ngân hàng từ URL"""
    url_lower = url.lower()
    for key in BANK_KNOWLEDGE:
        if key in url_lower:
            return key
    return None


def crawl_website(url, max_retries=2):
    """Crawl website với nhiều chiến lược fallback"""
    headers = random.choice(HEADERS_LIST)
    bank_key = get_bank_key(url)

    # Thử crawl thực tế trước
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.headers.update(headers)

            # Thêm cookies giả để vượt qua basic bot detection
            session.cookies.set("visited", "1")

            res = session.get(url, timeout=25, verify=False, allow_redirects=True)

            if res.status_code == 403 or res.status_code == 429:
                raise Exception(f"Blocked: HTTP {res.status_code}")

            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")

            # Xóa noise
            for tag in soup(["script", "style", "nav", "footer", "form", "iframe", "noscript"]):
                tag.decompose()

            structured = extract_structured_data(soup)
            text = soup.get_text(separator=" ", strip=True)

            # Nếu content quá ít → website có thể dùng JS rendering
            if len(text) < 500:
                raise Exception("Content too short - likely JS-rendered")

            full_text = f"""
TITLE: {soup.title.get_text(strip=True) if soup.title else ''}
URL: {url}
PRODUCTS: {structured['products']}
PROMOTIONS: {structured['promotions']}
DIGITAL: {structured['digital']}
RATES: {structured['rates']}
CONTENT: {text[:7000]}
"""
            print(f"✅ Crawled successfully: {len(full_text)} chars")
            return full_text[:9000]

        except Exception as e:
            print(f"⚠️ Crawl attempt {attempt+1} failed for {url}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(3)

    # FALLBACK: Dùng knowledge base nếu crawl thất bại
    if bank_key and bank_key in BANK_KNOWLEDGE:
        print(f"📚 Using knowledge base for {bank_key}")
        return build_from_knowledge(bank_key, url)

    print(f"❌ Complete failure for {url}")
    return None


def build_from_knowledge(bank_key, url):
    """Xây dựng content từ knowledge base khi crawl thất bại"""
    info = BANK_KNOWLEDGE[bank_key]
    products_text = " | ".join(info["known_products"])
    promos_text = " | ".join(info["promotions"])
    digital_text = " | ".join(info["digital"])

    return f"""
TITLE: {info['full_name']} - Website Chính Thức
URL: {url}
SOURCE: knowledge_base

PRODUCTS: {products_text}
PROMOTIONS: {promos_text}
DIGITAL: {digital_text}
RATES: Tiết kiệm {info['rates']['savings']}, Vay {info['rates']['loan']}

POSITIONING: {info['positioning']}
STRENGTHS: {' | '.join(info['strengths'])}
WEAKNESSES: {' | '.join(info['weaknesses'])}

CONTENT: {info['full_name']} cung cấp đầy đủ sản phẩm tài chính bao gồm:
Sản phẩm tiết kiệm và tiền gửi, cho vay cá nhân và doanh nghiệp,
thẻ tín dụng và ghi nợ, dịch vụ ngân hàng số {digital_text},
bảo hiểm và đầu tư. Lãi suất tiết kiệm: {info['rates']['savings']}.
Lãi suất vay: {info['rates']['loan']}.
"""


def extract_structured_data(soup):
    """Trích xuất dữ liệu có cấu trúc từ HTML"""
    data = {"products": [], "promotions": [], "digital": [], "rates": []}

    try:
        # Tìm sản phẩm từ các selector phổ biến
        product_selectors = [
            "[class*='product']", "[class*='service']", "[class*='san-pham']",
            ".product-card", ".service-item", "h2", "h3", "[class*='item']"
        ]
        seen = set()
        for selector in product_selectors:
            for elem in soup.select(selector)[:20]:
                try:
                    text = elem.get_text(strip=True)
                    if 10 < len(text) < 200 and text not in seen:
                        data["products"].append(text)
                        seen.add(text)
                except:
                    pass

        # Tìm khuyến mãi
        promo_selectors = [
            "[class*='promo']", "[class*='offer']", "[class*='khuyen-mai']",
            "[class*='campaign']", "[class*='banner']"
        ]
        for selector in promo_selectors:
            for elem in soup.select(selector)[:10]:
                text = elem.get_text(strip=True)
                if 15 < len(text) < 300:
                    data["promotions"].append(text[:150])

        # Tìm digital keywords
        body_text = soup.get_text().lower()
        digital_keywords = ["app", "mobile banking", "internet banking", "digital",
                            "e-banking", "chatbot", "qr code", "vnpay", "smartbanking"]
        data["digital"] = [kw for kw in digital_keywords if kw in body_text]

        # Tìm lãi suất
        rates = re.findall(r'(\d+\.?\d*)\s*%', body_text)
        data["rates"] = sorted(list(set(rates)))[:8]

    except Exception as e:
        print(f"Error in extract_structured_data: {e}")

    return data
