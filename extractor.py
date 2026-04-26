import json
import re
from llm import call_ai_api, clean_json


def get_entity_info(url):
    """Xác định tên tổ chức từ URL"""
    KNOWN_ENTITIES = {
        # Ngân hàng Việt Nam
        'techcombank': {'name': 'Techcombank', 'code': 'TCB', 'type': 'bank'},
        'bidv': {'name': 'BIDV', 'code': 'BIDV', 'type': 'bank'},
        'vietinbank': {'name': 'VietinBank', 'code': 'CTG', 'type': 'bank'},
        'vietcombank': {'name': 'Vietcombank', 'code': 'VCB', 'type': 'bank'},
        'mbbank': {'name': 'MB Bank', 'code': 'MBB', 'type': 'bank'},
        'mb.com': {'name': 'MB Bank', 'code': 'MBB', 'type': 'bank'},
        'vpbank': {'name': 'VPBank', 'code': 'VPB', 'type': 'bank'},
        'acb': {'name': 'ACB', 'code': 'ACB', 'type': 'bank'},
        'sacombank': {'name': 'Sacombank', 'code': 'STB', 'type': 'bank'},
        'hdbank': {'name': 'HDBank', 'code': 'HDB', 'type': 'bank'},
        'tpbank': {'name': 'TPBank', 'code': 'TPB', 'type': 'bank'},
        'msb': {'name': 'MSB', 'code': 'MSB', 'type': 'bank'},
        'ocb': {'name': 'OCB', 'code': 'OCB', 'type': 'bank'},
        'seabank': {'name': 'SeABank', 'code': 'SSB', 'type': 'bank'},
        'abbank': {'name': 'ABBank', 'code': 'ABB', 'type': 'bank'},
        'bacabank': {'name': 'BacABank', 'code': 'BAB', 'type': 'bank'},
        'agribank': {'name': 'Agribank', 'code': 'AGB', 'type': 'bank'},
        'vib': {'name': 'VIB', 'code': 'VIB', 'type': 'bank'},
        'shinhan': {'name': 'Shinhan Bank', 'code': 'SHB_VN', 'type': 'bank'},
        'hsbc': {'name': 'HSBC Vietnam', 'code': 'HSBC', 'type': 'bank'},
        'citibank': {'name': 'Citibank Vietnam', 'code': 'CITI', 'type': 'bank'},
        'standardchartered': {'name': 'Standard Chartered VN', 'code': 'SCB', 'type': 'bank'},
        'lpbank': {'name': 'LPBank', 'code': 'LPB', 'type': 'bank'},
        'pvcombank': {'name': 'PVcomBank', 'code': 'PVC', 'type': 'bank'},
        'eximbank': {'name': 'Eximbank', 'code': 'EIB', 'type': 'bank'},
        # Fintech / Ví điện tử
        'momo': {'name': 'MoMo', 'code': 'MOMO', 'type': 'fintech'},
        'zalopay': {'name': 'ZaloPay', 'code': 'ZLP', 'type': 'fintech'},
        'vnpay': {'name': 'VNPAY', 'code': 'VNP', 'type': 'fintech'},
        'payoo': {'name': 'Payoo', 'code': 'PAY', 'type': 'fintech'},
        'shopeepay': {'name': 'ShopeePay', 'code': 'SPP', 'type': 'fintech'},
        # Bảo hiểm
        'baoviethealthcare': {'name': 'Bảo Việt Healthcare', 'code': 'BVH', 'type': 'insurance'},
        'baoviet': {'name': 'Bảo Việt', 'code': 'BVH', 'type': 'insurance'},
        'prudential': {'name': 'Prudential Vietnam', 'code': 'PRU', 'type': 'insurance'},
        'manulife': {'name': 'Manulife Vietnam', 'code': 'MFC', 'type': 'insurance'},
        'aia': {'name': 'AIA Vietnam', 'code': 'AIA', 'type': 'insurance'},
        'sunlife': {'name': 'Sun Life Vietnam', 'code': 'SLF', 'type': 'insurance'},
    }

    url_lower = url.lower()
    for key, info in KNOWN_ENTITIES.items():
        if key in url_lower:
            return info

    # Tự động parse domain
    try:
        domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace("www2.", "")
        # Bỏ TLD
        name_raw = domain.split(".")[0]
        name = name_raw.upper()
        # Phát hiện type từ domain
        entity_type = 'company'
        if any(w in url_lower for w in ['bank', 'ngan-hang', 'financial', 'finance', 'vib', 'acb', 'msb']):
            entity_type = 'bank'
        elif any(w in url_lower for w in ['insurance', 'bao-hiem', 'life', 'assurance']):
            entity_type = 'insurance'
        elif any(w in url_lower for w in ['pay', 'wallet', 'fintech', 'ví']):
            entity_type = 'fintech'
        return {'name': name, 'code': name[:4].upper(), 'type': entity_type}
    except:
        return {'name': 'UNKNOWN', 'code': 'UNK', 'type': 'company'}


def extract_data(text, url):
    """
    Phân tích dữ liệu thực tế từ content crawl.
    KHÔNG có fallback knowledge base hay mock data.
    """
    entity_info = get_entity_info(url)

    if not text or len(text) < 100:
        return create_error_response(entity_info, url, "Không crawl được dữ liệu từ website")

    # Detect crawl source
    source_type = "live_crawl"
    if "SOURCE: live_crawl_requests" in text:
        source_type = "live_crawl_requests"

    entity_type = entity_info.get('type', 'company')

    # Prompt động theo loại tổ chức
    if entity_type == 'bank':
        category_guide = """
Categories cho ngân hàng:
- SAVINGS: Tiết kiệm, gửi tiền, tài khoản tiết kiệm, tiền gửi có kỳ hạn
- LOAN: Vay cá nhân, vay mua nhà, vay mua xe, vay tiêu dùng, tín dụng
- CARD: Thẻ tín dụng, thẻ ghi nợ, thẻ trả trước, thẻ Visa/Master
- DIGITAL: Mobile banking, Internet banking, app, ví điện tử, QR
- INSURANCE: Bảo hiểm nhân thọ, phi nhân thọ, bảo hiểm khoản vay
- INVESTMENT: Quỹ đầu tư, trái phiếu, chứng khoán, gold
- PAYMENT: Chuyển tiền, thanh toán hóa đơn, nạp tiền
- BUSINESS: Tài khoản doanh nghiệp, vay doanh nghiệp, LC/xuất nhập khẩu
- OTHER: Các sản phẩm/dịch vụ khác"""
    elif entity_type == 'insurance':
        category_guide = """
Categories cho bảo hiểm:
- LIFE: Bảo hiểm nhân thọ, bảo hiểm tử kỳ, bảo hiểm trọn đời
- HEALTH: Bảo hiểm sức khỏe, bảo hiểm y tế, bảo hiểm tai nạn
- INVESTMENT: Bảo hiểm đầu tư, bảo hiểm liên kết đầu tư
- SAVINGS: Bảo hiểm tiết kiệm, bảo hiểm trẻ em, giáo dục
- NON_LIFE: Bảo hiểm xe cộ, tài sản, du lịch, hàng hóa
- BUSINESS: Bảo hiểm doanh nghiệp, trách nhiệm, tài sản công ty
- OTHER: Các sản phẩm khác"""
    elif entity_type == 'fintech':
        category_guide = """
Categories cho fintech/ví điện tử:
- PAYMENT: Thanh toán QR, chuyển tiền, nạp tiền, thanh toán hóa đơn
- SAVINGS: Tiết kiệm, gửi tiền, tích lũy
- LOAN: Vay tiêu dùng, mua trước trả sau (BNPL), tín dụng
- INVESTMENT: Đầu tư, mua vàng, quỹ
- CASHBACK: Hoàn tiền, điểm thưởng, ưu đãi
- MERCHANT: Giải pháp cho merchant, POS, QR
- OTHER: Các dịch vụ khác"""
    else:
        category_guide = """
Categories cho công ty:
- PRODUCT: Sản phẩm chính
- SERVICE: Dịch vụ chính
- SUBSCRIPTION: Gói đăng ký, thuê bao
- SOLUTION: Giải pháp doanh nghiệp
- SUPPORT: Hỗ trợ, bảo hành, dịch vụ sau bán hàng
- DIGITAL: Sản phẩm/dịch vụ số, app, platform
- OTHER: Khác"""

    prompt = f"""Bạn là chuyên gia phân tích sản phẩm & chiến lược kinh doanh. Phân tích THỰC TẾ dữ liệu đã crawl từ website sau.

TỔ CHỨC: {entity_info['name']} ({entity_info['code']}) - Loại: {entity_type}
URL: {url}
NGUỒN DỮ LIỆU: {source_type}

=== DỮ LIỆU CRAWL THỰC TẾ ===
{text[:8500]}

{category_guide}

Phân tích KỸ CÀNG dựa trên dữ liệu crawl thực tế ở trên. Trích xuất tất cả sản phẩm/dịch vụ tìm thấy.
Trả về DUY NHẤT JSON (không có text nào bên ngoài):

{{
  "entity_name": "{entity_info['name']}",
  "entity_code": "{entity_info['code']}",
  "entity_type": "{entity_type}",
  "website": "{url}",
  "products": [
    {{
      "category": "CATEGORY_CODE",
      "name": "Tên sản phẩm/dịch vụ cụ thể tìm thấy",
      "features": ["Tính năng 1 tìm thấy", "Tính năng 2"],
      "target": "Đối tượng khách hàng",
      "highlight": "Điểm nổi bật"
    }}
  ],
  "pricing": {{
    "interest_rates": {{
      "savings_rate": "X%/năm",
      "loan_rate": "X%/năm",
      "other_rates": "..."
    }},
    "fees": ["Phí 1", "Phí 2"],
    "promotions": [
      {{
        "name": "Tên chương trình KM",
        "benefit": "Lợi ích cụ thể (số tiền, %, điều kiện)",
        "target_segment": "Đối tượng",
        "validity": "Thời hạn nếu có"
      }}
    ]
  }},
  "digital_capabilities": [
    {{
      "name": "Tên sản phẩm/tính năng số",
      "description": "Mô tả tính năng"
    }}
  ],
  "strategic_analysis": {{
    "positioning": "Định vị thương hiệu thực tế từ website",
    "target_segments": ["Phân khúc 1", "Phân khúc 2"],
    "key_differentiators": ["Điểm khác biệt 1 rút ra từ dữ liệu", "Điểm 2"],
    "value_proposition": "Giá trị cốt lõi",
    "pricing_strategy": "Chiến lược giá",
    "distribution_strategy": "Kênh phân phối",
    "marketing_approach": "Cách tiếp thị nhận thấy từ website"
  }},
  "competitive_assessment": {{
    "strengths": ["Điểm mạnh 1 dựa trên dữ liệu", "Điểm mạnh 2", "Điểm mạnh 3"],
    "weaknesses": ["Hạn chế 1", "Hạn chế 2"],
    "market_position": "Leader/Challenger/Follower/Niche",
    "competitive_threat_level": "High/Medium/Low",
    "unique_selling_points": ["USP 1", "USP 2"]
  }},
  "data_confidence": "high/medium/low",
  "data_notes": "Ghi chú về chất lượng dữ liệu crawl"
}}

QUAN TRỌNG:
- Chỉ trích xuất những gì THỰC SỰ có trong dữ liệu crawl, không bịa thêm
- Nếu không tìm thấy lãi suất cụ thể, để trống hoặc ghi "Không tìm thấy"
- Tối thiểu phải có 5-15 sản phẩm/dịch vụ từ dữ liệu
- data_confidence: high nếu có nhiều dữ liệu rõ ràng, medium nếu một phần, low nếu ít
- Chỉ trả về JSON, không có text nào khác"""

    try:
        print(f"🤖 AI extracting data for {entity_info['name']}...")
        ai_content = call_ai_api(prompt, max_tokens=3500)
        parsed = clean_json(ai_content)

        if not parsed:
            raise Exception("Cannot parse JSON from AI response")

        # Normalize fields
        parsed.setdefault("entity_name", entity_info['name'])
        parsed.setdefault("entity_code", entity_info['code'])
        parsed.setdefault("entity_type", entity_type)
        parsed.setdefault("products", [])
        parsed.setdefault("pricing", {"promotions": [], "fees": [], "interest_rates": {}})
        parsed.setdefault("digital_capabilities", [])
        parsed.setdefault("strategic_analysis", {})
        parsed.setdefault("competitive_assessment", {})
        parsed.setdefault("data_confidence", "medium")

        # Backward compat: map entity_name -> bank_name, entity_code -> bank_code
        parsed["bank_name"] = parsed["entity_name"]
        parsed["bank_code"] = parsed["entity_code"]
        parsed["promotions"] = parsed.get("pricing", {}).get("promotions", [])
        parsed["interest_rates"] = parsed.get("pricing", {}).get("interest_rates", {})

        # Digital capabilities normalization
        dc = parsed.get("digital_capabilities", [])
        if dc and isinstance(dc[0], dict):
            parsed["digital_capabilities"] = [d.get("name", "") for d in dc if d.get("name")]

        n_products = len(parsed.get("products", []))
        confidence = parsed.get("data_confidence", "medium")
        if n_products >= 10 and confidence == "high":
            quality = "deep"
        elif n_products >= 5:
            quality = "good"
        elif n_products >= 2:
            quality = "limited"
        else:
            quality = "limited"

        print(f"✅ Extracted: {n_products} products, quality={quality}, confidence={confidence}")

        return {
            "url": url,
            "analysis": parsed,
            "extraction_quality": quality,
            "source": source_type,
            "entity_type": entity_type
        }

    except Exception as e:
        print(f"❌ AI extraction failed for {entity_info['name']}: {str(e)}")
        return create_error_response(entity_info, url, str(e))


def create_error_response(entity_info, url="", error_msg=""):
    return {
        "url": url,
        "analysis": {
            "entity_name": entity_info['name'],
            "entity_code": entity_info['code'],
            "entity_type": entity_info.get('type', 'company'),
            "bank_name": entity_info['name'],
            "bank_code": entity_info['code'],
            "products": [],
            "interest_rates": {},
            "promotions": [],
            "digital_capabilities": [],
            "strategic_analysis": {
                "positioning": "Không thể phân tích",
                "target_segments": [],
                "key_differentiators": [],
                "pricing_strategy": "Unknown",
                "distribution_strategy": "Unknown",
                "marketing_approach": "Unknown"
            },
            "competitive_assessment": {
                "strengths": [],
                "weaknesses": [error_msg or "Website không khả dụng hoặc không thể crawl"],
                "market_position": "Unknown",
                "competitive_threat_level": "Unknown"
            },
            "data_confidence": "none",
            "data_notes": error_msg
        },
        "extraction_quality": "error",
        "source": "error",
        "entity_type": entity_info.get('type', 'company')
    }
