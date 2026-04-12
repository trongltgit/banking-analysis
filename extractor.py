import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000, retries=3):
    """Gọi Groq API với retry logic"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK environment variable not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system", 
                "content": "Bạn là chuyên gia phân tích ngân hàng cấp cao. Trả về JSON hợp lệ, không giải thích."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
            
            if res.status_code == 429:
                wait_time = 2 ** (attempt + 2)  # 4, 8, 16 seconds
                print(f"      ⏳ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise Exception(f"Groq API error: {str(e)}")
    
    raise Exception("Max retries exceeded")

def clean_json(text):
    """Làm sạch JSON từ response"""
    if not text:
        return None
    
    try:
        return json.loads(text)
    except:
        # Tìm JSON trong markdown code blocks
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
    return None

def extract_data(text, url):
    """Deep Learning Extraction - Phân tích chuyên sâu thực sự"""
    
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".com", "").replace(".vn", "").upper()
    
    # Nếu crawl lỗi, vẫn cố gắng phân tích những gì có
    crawl_error = text.startswith("ERROR_CRAWL")
    
    prompt = f"""PHÂN TÍCH CHUYÊN SÂU WEBSITE NGÂN HÀNG - DEEP LEARNING AI

Bạn là CHUYÊN GIA PHÂN TÍCH NGÂN HÀNG với 20 năm kinh nghiệm tại McKinsey & BCG.

NHIỆM VỤ: Phân tích sâu nội dung website và trích xuất TOÀN BỘ sản phẩm, chiến lược, định vị.

URL: {url}
CONTENT: {text[:10000]}

{"LƯU Ý: Crawl gặp lỗi, nhưng hãy phân tích những gì có trong content để suy luận." if crawl_error else ""}

YÊU CẦU PHÂN TÍCH CHUYÊN SÂU:

1. TÊN NGÂN HÀNG: Xác định chính xác tên đầy đủ, mã chứng khoán nếu có

2. DANH MỤC SẢN PHẨM ĐẦY ĐỦ (Tối thiểu 8-15 sản phẩm):
   - TIẾT KIỆM: Tiết kiệm thường, online, tích lũy, linh hoạt, điện tử
   - CHO VAY: Mua nhà, tiêu dùng tín chấp, thế chấp, kinh doanh, ô tô, du học, thấu chi
   - THẺ: Tín dụng, ghi nợ, đồng thương hiệu, hoàn tiền, tích điểm, premium
   - NGÂN HÀNG SỐ: Mobile banking, Internet banking, QR Pay, Face ID, AI chatbot
   - BẢO HIỂM: Nhân thọ, sức khỏe, tai nạn, xe, bancassurance
   - ĐẦU TƯ: Chứng khoán, quỹ đầu tư, trái phiếu, vàng, ngoại tệ
   - DỊCH VỤ KHÁC: Chuyển tiền quốc tế, bảo lãnh, tư vấn tài chính, quản lý tài sản

3. LÃI SUẤT: Trích xuất tất cả lãi suất được đề cập

4. CHƯƠNG TRÌNH KHUYẾN MÃI: Liệt kê tất cả CTKM (tên, lợi ích, đối tượng, thời hạn)

5. PHÂN TÍCH CHIẾN LƯỢC:
   - Định vị thương hiệu (positioning statement)
   - Phân khúc khách hàng mục tiêu (target segments)
   - Điểm khác biệt cạnh tranh (key differentiators)
   - Chiến lược giá (pricing strategy)
   - Chiến lược phân phối (distribution channels)
   - Chiến lược marketing hiện tại

6. ĐÁNH GIÁ CẠNH TRANH:
   - Điểm mạnh chiến lược (3-5 điểm)
   - Điểm yếu/điểm cần cải thiện (2-3 điểm)
   - Vị thế thị trường (Leader/Challenger/Follower/Niche)
   - Mức độ đe dọa cạnh tranh (High/Medium/Low)

OUTPUT FORMAT - JSON STRICT:
{{
    "bank_name": "Tên đầy đủ",
    "bank_code": "Mã CK",
    "products": [
        {{
            "category": "SAVINGS/LOAN/CARD/DIGITAL/INSURANCE/INVESTMENT/OTHER",
            "name": "Tên sản phẩm cụ thể",
            "features": ["đặc điểm 1", "đặc điểm 2", "lợi ích chính"],
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
            "benefit": "Lợi ích cụ thể",
            "target_segment": "Đối tượng áp dụng",
            "duration": "Thời gian",
            "channels": ["Online", "Branch", "App"]
        }}
    ],
    "digital_capabilities": [
        "Tính năng cụ thể: VD - Face ID login, AI chatbot, Biometric payment, Open API"
    ],
    "strategic_analysis": {{
        "positioning": "Định vị thương hiệu chi tiết",
        "target_segments": ["Phân khúc 1", "Phân khúc 2", "Phân khúc 3"],
        "key_differentiators": ["Điểm khác biệt 1", "Điểm khác biệt 2", "Điểm khác biệt 3"],
        "pricing_strategy": "Chiến lược giá chi tiết",
        "distribution_strategy": "Chiến lược kênh phân phối",
        "marketing_strategy": "Chiến lược marketing hiện tại"
    }},
    "competitive_assessment": {{
        "strengths": ["Điểm mạnh chiến lược 1", "Điểm mạnh 2", "Điểm mạnh 3", "Điểm mạnh 4", "Điểm mạnh 5"],
        "weaknesses": ["Điểm yếu 1", "Điểm yếu 2", "Điểm yếu 3"],
        "market_position": "Leader/Challenger/Follower/Niche player",
        "competitive_threat_level": "High/Medium/Low"
    }},
    "product_gaps_vs_market": ["Sản phẩm còn thiếu so với thị trường"]
}}

QUY TẮC NGHIÊM NGẶT:
- Chỉ dùng dữ liệu có trong nội dung, không bịa đặt
- Nếu thiếu thông tin, để null hoặc [] chứ không đoán
- Phải liệt kê TẤT CẢ sản phẩm tìm thấy, không giới hạn số lượng
- Phân tích chiến lược phải dựa trên evidence từ website
- Trả về JSON hợp lệ, không markdown, không giải thích ngoài JSON"""

    try:
        # Model mạnh nhất cho deep analysis
        content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000, retries=3)
        parsed = clean_json(content)
        
        if not parsed:
            # Retry với model nhỏ hơn nếu model lớn fail
            print("      🔄 Retry with alternative model...")
            content = call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=3000, retries=2)
            parsed = clean_json(content)
        
        if not parsed:
            raise Exception("Cannot parse AI response - invalid JSON format")
            
    except Exception as e:
        # KHÔNG fallback - báo lỗi thật để user biết
        raise Exception(f"AI extraction failed for {url}: {str(e)}")

    # Normalize structure
    analysis = parsed
    
    # Ensure nested objects exist
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
    for key in ["products", "promotions", "digital_capabilities", "product_gaps_vs_market"]:
        if not isinstance(analysis.get(key), list):
            analysis[key] = []
    
    # Quality assessment
    product_count = len(analysis.get("products", []))
    quality = "deep" if product_count >= 10 else "good" if product_count >= 6 else "limited"
    
    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }
