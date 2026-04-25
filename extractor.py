import json
import re
from llm import call_ai_api, clean_json


BANK_MAPPING = {
    'techcombank': {'name': 'Techcombank', 'code': 'TCB'},
    'bidv':        {'name': 'BIDV',        'code': 'BIDV'},
    'vietinbank':  {'name': 'VietinBank',  'code': 'CTG'},
    'vietcombank': {'name': 'Vietcombank', 'code': 'VCB'},
}


def get_bank_info(url):
    url_lower = url.lower()
    for key, info in BANK_MAPPING.items():
        if key in url_lower:
            return info
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").split(".")[0]
    return {'name': domain.upper(), 'code': 'UNKNOWN'}


def extract_data(text, url):
    """Phân tích dữ liệu từ content crawl / knowledge base"""
    bank_info = get_bank_info(url)

    if not text or len(text) < 50:
        return create_error_response(bank_info, url)

    is_knowledge_base = "SOURCE: knowledge_base" in text
    source_note = "(Dữ liệu từ knowledge base - website chặn bot)" if is_knowledge_base else "(Dữ liệu crawl trực tiếp)"

    prompt = f"""Bạn là chuyên gia phân tích ngân hàng Việt Nam. Hãy phân tích dữ liệu sau của ngân hàng {bank_info['name']} ({bank_info['code']}).

{source_note}
URL: {url}

DỮ LIỆU:
{text[:8000]}

Hãy phân tích kỹ và trả về JSON với cấu trúc chính xác sau (KHÔNG có text nào bên ngoài JSON):
{{
  "bank_name": "{bank_info['name']}",
  "bank_code": "{bank_info['code']}",
  "products": [
    {{"category": "SAVINGS", "name": "Tên sản phẩm cụ thể", "features": ["tính năng 1", "tính năng 2"]}},
    {{"category": "LOAN", "name": "Tên sản phẩm", "features": ["đặc điểm"]}},
    {{"category": "CARD", "name": "Tên thẻ", "features": ["đặc điểm"]}},
    {{"category": "DIGITAL", "name": "Tên dịch vụ số", "features": ["tính năng"]}},
    {{"category": "INSURANCE", "name": "Tên bảo hiểm", "features": ["đặc điểm"]}},
    {{"category": "INVESTMENT", "name": "Tên sản phẩm đầu tư", "features": ["đặc điểm"]}}
  ],
  "interest_rates": {{
    "savings_min": "X%",
    "savings_max": "Y%",
    "loan_min": "X%",
    "loan_max": "Y%"
  }},
  "promotions": [
    {{"name": "Tên chương trình", "benefit": "Lợi ích cụ thể (số tiền/%, ưu đãi)", "target_segment": "Đối tượng"}}
  ],
  "digital_capabilities": ["Tên ứng dụng/dịch vụ số 1", "dịch vụ 2"],
  "strategic_analysis": {{
    "positioning": "Định vị thương hiệu cụ thể",
    "target_segments": ["Phân khúc khách hàng 1", "phân khúc 2"],
    "key_differentiators": ["Điểm khác biệt 1", "điểm 2"],
    "pricing_strategy": "Chiến lược giá cụ thể",
    "distribution_strategy": "Chiến lược phân phối",
    "marketing_strategy": "Chiến lược marketing"
  }},
  "competitive_assessment": {{
    "strengths": ["Điểm mạnh 1", "điểm mạnh 2", "điểm mạnh 3"],
    "weaknesses": ["Điểm yếu 1", "điểm yếu 2"],
    "market_position": "Leader/Challenger/Follower",
    "competitive_threat_level": "High/Medium/Low"
  }}
}}

YÊU CẦU:
- Tối thiểu 8-12 sản phẩm cụ thể với tên thực tế
- Lãi suất phải có con số cụ thể
- Ít nhất 3 khuyến mãi với lợi ích rõ ràng
- Phân tích chiến lược dựa trên thực tế ngân hàng
- CHỈ trả về JSON, không có text nào khác"""

    try:
        print(f"🤖 AI analyzing {bank_info['name']}...")
        ai_content = call_ai_api(prompt, max_tokens=3000)
        parsed = clean_json(ai_content)

        if not parsed:
            raise Exception("Cannot parse JSON from AI response")

        # Đảm bảo các field bắt buộc
        parsed.setdefault("bank_name", bank_info['name'])
        parsed.setdefault("bank_code", bank_info['code'])
        parsed.setdefault("products", [])
        parsed.setdefault("promotions", [])
        parsed.setdefault("digital_capabilities", [])
        parsed.setdefault("interest_rates", {})
        parsed.setdefault("strategic_analysis", {})
        parsed.setdefault("competitive_assessment", {})

        n_products = len(parsed.get("products", []))
        quality = "deep" if n_products >= 8 else "good" if n_products >= 4 else "limited"

        return {
            "url": url,
            "analysis": parsed,
            "extraction_quality": quality,
            "source": "knowledge_base" if is_knowledge_base else "live_crawl"
        }

    except Exception as e:
        print(f"❌ AI extraction failed for {bank_info['name']}: {str(e)}")
        return create_error_response(bank_info, url)


def create_error_response(bank_info, url=""):
    return {
        "url": url,
        "analysis": {
            "bank_name": bank_info['name'],
            "bank_code": bank_info['code'],
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
                "marketing_strategy": "Unknown"
            },
            "competitive_assessment": {
                "strengths": [],
                "weaknesses": ["Website không khả dụng hoặc không thể phân tích"],
                "market_position": "Unknown",
                "competitive_threat_level": "Unknown"
            }
        },
        "extraction_quality": "error",
        "source": "error"
    }
