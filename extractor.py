import os
import json
import re
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=2000):
    """Gọi Groq API với error handling"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia phân tích ngân hàng cấp cao. Trả về JSON hợp lệ, không giải thích."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }
    
    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"Groq API error: {str(e)}")

def clean_json(text):
    """Làm sạch JSON response"""
    if not text:
        return None
    
    try:
        return json.loads(text)
    except:
        # Tìm JSON trong text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

def extract_data(text, url):
    """Deep Learning Extraction - Phân tích chuyên sâu"""
    
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".com", "").replace(".vn", "").upper()
    
    prompt = f"""PHÂN TÍCH CHUYÊN SÂU WEBSITE NGÂN HÀNG - DEEP LEARNING AI

Bạn là CHUYÊN GIA PHÂN TÍCH NGÂN HÀNG với 20 năm kinh nghiệm tại McKinsey & BCG.

NHIỆM VỤ: Phân tích sâu nội dung website và trích xuất TOÀN BỘ sản phẩm, dịch vụ, chiến lược.

NỘI DUNG WEBSITE:
{text[:8000]}

YÊU CẦU PHÂN TÍCH CHUYÊN SÂU:

1. TÊN NGÂN HÀNG: Xác định chính xác tên đầy đủ, mã chứng khoán nếu có

2. DANH MỤC SẢN PHẨM ĐẦY ĐỦ (Tối thiểu 8-12 sản phẩm nếu website có đủ thông tin):
   - TIẾT KIỆM: Tiết kiệm thường, tiết kiệm online, tiết kiệm tích lũy, tiết kiệm linh hoạt, tiết kiệm điện tử
   - CHO VAY: Vay mua nhà, vay tiêu dùng tín chấp, vay tiêu dùng thế chấp, vay kinh doanh, vay ô tô, vay du học, vay cầm cố, vay thấu chi
   - THẺ: Thẻ tín dụng, thẻ ghi nợ, thẻ đồng thương hiệu, thẻ tín dụng hoàn tiền, thẻ tín dụng tích điểm, thẻ premium/elite
   - NGÂN HÀNG SỐ: Mobile banking, Internet banking, SMS banking, QR Pay, Biometric auth, Open API
   - BẢO HIỂM: Bảo hiểm nhân thọ, bảo hiểm sức khỏe, bảo hiểm tai nạn, bảo hiểm xe, bancassurance
   - ĐẦU TƯ: Chứng khoán, quỹ đầu tư, trái phiếu, vàng, ngoại tệ, tiền gửi có kỳ hạn cao cấp
   - DỊCH VỤ KHÁC: Chuyển tiền quốc tế, Western Union, bảo lãnh thanh toán, tư vấn tài chính, quản lý tài sản

3. LÃI SUẤT: Trích xuất chính xác tất cả lãi suất được đề cập (tiết kiệm, vay, thẻ)

4. CHƯƠNG TRÌNH KHUYẾN MÃI: Liệt kê tất cả CTKM đang chạy (tên, lợi ích, đối tượng, thời hạn)

5. KHẢ NĂNG SỐ HÓA: Đánh giá mức độ digital (app features, AI, automation)

6. PHÂN TÍCH CHIẾN LƯỢC TỪNG NGÂN HÀNG:
   - Định vị thương hiệu (positioning)
   - Phân khúc khách hàng mục tiêu
   - Điểm mạnh cạnh tranh (competitive advantages)
   - Điểm yếu/điểm cần cải thiện
   - Chiến lược giá cả
   - Chiến lược phân phối (kênh phân phối)
   - Chiến lược marketing đang thực hiện

OUTPUT FORMAT - JSON STRICT:
{{
    "bank_name": "Tên đầy đủ",
    "bank_code": "Mã CK",
    "products": [
        {{
            "category": "SAVINGS/LOAN/CARD/DIGITAL/INSURANCE/INVESTMENT/OTHER",
            "name": "Tên sản phẩm cụ thể",
            "features": ["đặc điểm 1", "đặc điểm 2", "lợi ích"],
            "target_segment": "Khách hàng mục tiêu",
            "competitive_edge": "Lợi thế so với đối thủ",
            "price_positioning": "Cao/trung bình/thấp hơn thị trường"
        }}
    ],
    "interest_rates": {{
        "savings_1m": "X%",
        "savings_3m": "X%", 
        "savings_6m": "X%",
        "savings_12m": "X%",
        "loan_personal": "X%",
        "loan_home": "X%",
        "loan_business": "X%",
        "credit_card": "X%"
    }},
    "promotions": [
        {{
            "name": "Tên CTKM",
            "description": "Mô tả chi tiết",
            "benefit": "Lợi ích cụ thể (VD: Hoàn tiền 10%)",
            "target_segment": "Đối tượng áp dụng",
            "duration": "Thời gian",
            "channels": ["Online", "Branch", "App"]
        }}
    ],
    "digital_capabilities": [
        "Tính năng cụ thể: VD - Face ID login, AI chatbot, Biometric payment"
    ],
    "strategic_analysis": {{
        "positioning": "Định vị thương hiệu chi tiết",
        "target_segments": ["Phân khúc 1", "Phân khúc 2"],
        "key_differentiators": ["Điểm khác biệt 1", "Điểm khác biệt 2"],
        "pricing_strategy": "Chiến lược giá",
        "distribution_strategy": "Chiến lược kênh phân phối",
        "marketing_strategy": "Chiến lược marketing hiện tại"
    }},
    "competitive_assessment": {{
        "strengths": ["Điểm mạnh chiến lược 1", "Điểm mạnh 2", "Điểm mạnh 3"],
        "weaknesses": ["Điểm yếu 1", "Điểm yếu 2"],
        "market_position": "Leader/Challenger/Follower/Niche player",
        "competitive_threat_level": "High/Medium/Low"
    }},
    "product_gaps_vs_market": ["Sản phẩm còn thiếu so với thị trường"]
}}

QUY TẮC NGHIÊM NGẶT:
- Không bịa đặt: Chỉ dùng dữ liệu có trong nội dung
- Nếu không có thông tin cụ thể, để null hoặc [] chứ không đoán
- Phải liệt kê TẤT CẢ sản phẩm tìm thấy, không giới hạn số lượng
- Phân tích chiến lược phải dựa trên evidence từ website"""

    try:
        # Thử model mạnh nhất trước
        content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000)
        parsed = clean_json(content)
        
        if not parsed or len(parsed.get("products", [])) < 3:
            # Fallback to smaller model nếu model lớn fail
            content = call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=3000)
            parsed = clean_json(content)
        
        if not parsed:
            raise Exception("Cannot parse AI response")
            
    except Exception as e:
        print(f"❌ AI extraction failed: {e}")
        # Return structure nhưng đánh dấu lỗi
        return {
            "url": url,
            "analysis": {
                "bank_name": domain,
                "bank_code": None,
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "strategic_analysis": {
                    "positioning": f"Error: {str(e)[:100]}",
                    "target_segments": [],
                    "key_differentiators": [],
                    "pricing_strategy": "Unknown",
                    "distribution_strategy": "Unknown",
                    "marketing_strategy": "Unknown"
                },
                "competitive_assessment": {
                    "strengths": [],
                    "weaknesses": ["AI extraction failed"],
                    "market_position": "Unknown",
                    "competitive_threat_level": "Unknown"
                },
                "product_gaps_vs_market": []
            },
            "extraction_quality": "error",
            "error": str(e)
        }

    # Normalize và đảm bảo đủ fields
    analysis = parsed
    
    # Đảm bảo strategic_analysis tồn tại
    if "strategic_analysis" not in analysis:
        analysis["strategic_analysis"] = {
            "positioning": analysis.get("positioning", "Unknown"),
            "target_segments": [],
            "key_differentiators": [],
            "pricing_strategy": "Unknown",
            "distribution_strategy": "Unknown",
            "marketing_strategy": "Unknown"
        }
    
    if "competitive_assessment" not in analysis:
        analysis["competitive_assessment"] = {
            "strengths": analysis.get("strengths", []),
            "weaknesses": analysis.get("weaknesses", []),
            "market_position": "Unknown",
            "competitive_threat_level": "Unknown"
        }
    
    # Normalize arrays
    for key in ["products", "promotions", "digital_capabilities"]:
        if not isinstance(analysis.get(key), list):
            analysis[key] = []
    
    # Quality assessment
    product_count = len(analysis.get("products", []))
    quality = "deep" if product_count >= 8 else "good" if product_count >= 4 else "limited"
    
    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }
