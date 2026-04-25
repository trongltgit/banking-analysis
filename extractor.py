def extract_data(text, url, structured_data=None):
    """Phân tích dữ liệu từ content crawl được"""
    
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".vn", "").replace(".com", "")
    
    bank_mapping = {
        'techcombank': {'name': 'Techcombank', 'code': 'TCB'},
        'bidv': {'name': 'BIDV', 'code': 'BIDV'},
        'vietinbank': {'name': 'VietinBank', 'code': 'CTG'},
        'vietcombank': {'name': 'Vietcombank', 'code': 'VCB'},
    }
    
    bank_info = bank_mapping.get(domain.lower(), {'name': domain.upper(), 'code': 'UNKNOWN'})
    
    if text.startswith("ERROR_CRAWL") or len(text) < 100:
        return create_error_response(bank_info)
    
    content = text[:8000]
    
    # Thêm dữ liệu có cấu trúc vào prompt
    structured_context = ""
    if structured_data:
        structured_context = f"""
DỮ LIỆU CÓ CẤU TRÚC ĐÃ TRÍCH XUẤT:
- Sản phẩm tìm được: {json.dumps(structured_data.get('products', []), ensure_ascii=False)}
- Khuyến mãi: {json.dumps(structured_data.get('promotions', []), ensure_ascii=False)}
- Dịch vụ Digital: {structured_data.get('digital_services', [])}
- Lãi suất: {structured_data.get('interest_rates', {})}
"""
    
    prompt = f"""Phân tích website ngân hàng {bank_info['name']} ({bank_info['code']}).
URL: {url}

{structured_context}

NỘI DUNG TRANG WEB:
{content}

HƯỚNG DẪN PHÂN TÍCH CHI TIẾT:
1. SẢN PHẨM: Liệt kê tất cả sản phẩm tìm được (tiết kiệm, vay, thẻ, bảo hiểm, đầu tư, digital)
   - Mỗi sản phẩm phải có: tên cụ thể, danh mục, đặc điểm chính
   - Ví dụ: "Tiết kiệm Tự do" (SAVINGS) - Gửi tiền linh hoạt, rút bất kỳ lúc nào

2. KHUYẾN MÃI: Tìm tất cả chương trình khuyến mãi hiện tại
   - Lợi ích cụ thể (% lãi suất, tiền thưởng, giảm phí)
   - Đối tượng áp dụng (khách hàng mới, VIP, sinh viên)

3. LÃISUẤT: Trích xuất tất cả lãi suất được công bố
   - Tiết kiệm: X% - Y%
   - Vay: X% - Y%
   - Thẻ: X% - Y%

4. DỊCH VỤ DIGITAL: Liệt kê tất cả kênh digital
   - App mobile, Internet banking, SMS banking, Chatbot, etc.

5. CHIẾN LƯỢC: Phân tích dựa trên dữ liệu thực tế
   - Định vị: Ngân hàng hướng tới khách hàng nào?
   - Điểm khác biệt: Ưu điểm so với đối thủ?
   - Mục tiêu: Phát triển sản phẩm nào?

Trả về JSON:
{{
  "bank_name": "{bank_info['name']}",
  "bank_code": "{bank_info['code']}",
  "products": [
    {{"category": "SAVINGS", "name": "Tiết kiệm Tự do", "features": ["Rút linh hoạt", "Lãi suất cạnh tranh"]}},
    {{"category": "LOAN", "name": "Vay Tín chỉ", "features": ["Lãi suất thấp", "Giải ngân nhanh"]}}
  ],
  "interest_rates": {{"savings_min": "4.5%", "savings_max": "6.5%", "loan_min": "6.5%", "loan_max": "12%"}},
  "promotions": [
    {{"name": "Mở tài khoản nhận 500K", "benefit": "Tiền thưởng 500.000đ", "target_segment": "Khách hàng mới"}}
  ],
  "digital_capabilities": ["App Mobile", "Internet Banking", "Chatbot 24/7"],
  "strategic_analysis": {{
    "positioning": "Ngân hàng số hóa, hướng tới khách hàng trẻ",
    "target_segments": ["Khách hàng trẻ", "Doanh nhân", "Startup"],
    "key_differentiators": ["App tốt nhất", "Lãi suất cao", "Phí thấp"],
    "pricing_strategy": "Cạnh tranh lãi suất, phí thấp",
    "distribution_strategy": "Digital-first, chi nhánh tối thiểu",
    "marketing_strategy": "Social media, influencer, content marketing"
  }},
  "competitive_assessment": {{
    "strengths": ["Công nghệ tốt", "Lãi suất cạnh tranh", "Dịch vụ khách hàng tốt"],
    "weaknesses": ["Mạng lưới chi nhánh nhỏ", "Ít sản phẩm bảo hiểm"],
    "market_position": "Challenger",
    "competitive_threat_level": "High"
  }}
}}

QUAN TRỌNG:
- Phải có ít nhất 5-10 sản phẩm cụ thể
- Lãi suất phải có con số cụ thể (không "cạnh tranh")
- Khuyến mãi phải có giá trị cụ thể
- Chiến lược phải dựa trên dữ liệu thực tế, không chung chung
"""

    try:
        print(f"🤖 Calling AI for {bank_info['name']}...")
        ai_content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=2500)
        parsed = clean_json(ai_content)
        
        if not parsed:
            ai_content = call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=2000)
            parsed = clean_json(ai_content)

        if not parsed:
            raise Exception("Cannot parse JSON from AI")

    except Exception as e:
        print(f"❌ AI extraction failed: {str(e)}")
        return create_error_response(bank_info)

    analysis = parsed
    analysis.setdefault("products", [])
    analysis.setdefault("promotions", [])
    analysis.setdefault("digital_capabilities", [])
    analysis.setdefault("interest_rates", {})
    analysis.setdefault("strategic_analysis", {})
    analysis.setdefault("competitive_assessment", {})
    
    quality = "deep" if len(analysis.get("products", [])) >= 8 else \
              "good" if len(analysis.get("products", [])) >= 4 else "limited"

    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }

def create_error_response(bank_info):
    return {
        "url": "",
        "analysis": {
            "bank_name": bank_info['name'],
            "bank_code": bank_info['code'],
            "products": [],
            "interest_rates": {},
            "promotions": [],
            "digital_capabilities": [],
            "strategic_analysis": {
                "positioning": "Không thể truy cập",
                "target_segments": [],
                "key_differentiators": [],
                "pricing_strategy": "Unknown",
                "distribution_strategy": "Unknown",
                "marketing_strategy": "Unknown"
            },
            "competitive_assessment": {
                "strengths": [],
                "weaknesses": ["Website không khả dụng"],
                "market_position": "Unknown",
                "competitive_threat_level": "Unknown"
            }
        },
        "extraction_quality": "error"
    }
