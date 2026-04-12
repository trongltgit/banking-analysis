from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])

def clean_json(text):
    """Trích xuất và làm sạch JSON từ response"""
    try:
        return json.loads(text)
    except:
        pass
    
    # Tìm JSON block
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{.*\}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if pattern.startswith('```') else match.group())
            except:
                continue
    
    return None

def extract_data(text, url):
    """Deep Learning Analysis - Phân tích chuyên sâu sản phẩm ngân hàng"""
    
    prompt = f"""
Bạn là CHUYÊN GIA PHÂN TÍCH NGÂN HÀNG CẤP CAO với 20 năm kinh nghiệm.

NHIỆM VỤ: Phân tích sâu website ngân hàng và trích xuất thông tin chiến lược.

QUY TẮC NGHIÊM NGẶT:
1. Chỉ trích xuất dữ liệu CÓ THỰC từ nội dung website
2. Không bịa đặt lãi suất - chỉ ghi nếu thấy rõ ràng
3. Phân loại sản phẩm theo chuẩn ngành ngân hàng
4. Đánh giá độ cạnh tranh qua các yếu tố: lãi suất, ưu đãi, digital experience

PHÂN LOẠI SẢN PHẨM CHUYÊN SÂU:
- TIẾT KIỆM: Tiết kiệm thường, tiết kiệm online, tiết kiệm tích lũy, tiết kiệm linh hoạt
- CHO VAY: Vay mua nhà, vay tiêu dùng, vay kinh doanh, vay ô tô, vay tín chấp
- THẺ: Thẻ tín dụng, thẻ ghi nợ, thẻ đồng thương hiệu, thẻ premium
- NGÂN HÀNG SỐ: App mobile, Internet banking, AI banking, Open banking
- BẢO HIỂM: Bảo hiểm nhân thọ, bảo hiểm phi nhân thọ, bancassurance
- ĐẦU TƯ: Chứng khoán, quỹ đầu tư, trái phiếu, vàng
- DỊCH VỤ KHÁC: Chuyển tiền quốc tế, bảo lãnh, tư vấn tài chính

INPUT:
URL: {url}
CONTENT: {text[:8000]}

OUTPUT JSON (chỉ JSON, không giải thích):
{{
    "bank_name": "Tên ngân hàng đầy đủ",
    "bank_code": "Mã niêm yết nếu có (VCB, TCB, BID...)",
    "products": [
        {{
            "category": "TIẾT KIỆM/CHO VAY/THẺ/NGÂN HÀNG SỐ/BẢO HIỂM/ĐẦU TƯ/KHÁC",
            "name": "Tên sản phẩm cụ thể",
            "features": ["đặc điểm 1", "đặc điểm 2"],
            "target_customer": "Khách hàng mục tiêu",
            "competitive_advantage": "Lợi thế cạnh tranh rõ ràng hoặc null"
        }}
    ],
    "interest_rates": {{
        "savings": "Lãi suất tiết kiệm nếu có",
        "loan": "Lãi suất cho vay nếu có",
        "credit_card": "Lãi suất thẻ tín dụng nếu có"
    }},
    "promotions": [
        {{
            "name": "Tên chương trình khuyến mãi",
            "benefit": "Lợi ích cụ thể",
            "target_segment": "Phân khúc khách hàng",
            "duration": "Thời hạn nếu có"
        }}
    ],
    "digital_capabilities": [
        "Tính năng digital banking nổi bật"
    ],
    "positioning": "Định vị thương hiệu ngân hàng",
    "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
    "weaknesses": ["Điểm yếu có thể suy luận từ thiếu sót website"]
}}
"""

    try:
        # First attempt
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Model mạnh nhất
            messages=[
                {
                    "role": "system", 
                    "content": "Bạn là chuyên gia ngân hàng. Trả về JSON hợp lệ, không markdown, không giải thích."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        content = res.choices[0].message.content.strip()
        parsed = clean_json(content)

        # Second attempt if failed
        if not parsed:
            repair_prompt = f"""
Sửa lỗi JSON sau thành JSON hợp lệ. Chỉ trả về JSON, không text khác:

{content}

Output phải là JSON object hợp lệ.
"""
            res2 = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": repair_prompt}],
                temperature=0,
                max_tokens=1500
            )
            parsed = clean_json(res2.choices[0].message.content.strip())

        # Final fallback
        if not parsed:
            parsed = create_fallback_structure(url)

        # Normalize structure
        parsed = normalize_structure(parsed, url)
        
        return {
            "url": url,
            "analysis": parsed,
            "extraction_quality": "deep" if len(parsed.get("products", [])) > 0 else "basic"
        }

    except Exception as e:
        return {
            "url": url,
            "analysis": create_fallback_structure(url),
            "error": str(e),
            "extraction_quality": "error"
        }

def create_fallback_structure(url):
    """Tạo cấu trúc mặc định khi extraction thất bại"""
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    return {
        "bank_name": domain.upper(),
        "bank_code": None,
        "products": [],
        "interest_rates": {},
        "promotions": [],
        "digital_capabilities": [],
        "positioning": "Không xác định được từ dữ liệu",
        "strengths": [],
        "weaknesses": ["Không truy cập được thông tin chi tiết"]
    }

def normalize_structure(data, url):
    """Chuẩn hóa cấu trúc dữ liệu"""
    default = create_fallback_structure(url)
    
    for key in default:
        if key not in data or data[key] is None:
            data[key] = default[key]
    
    # Ensure arrays
    for arr_key in ["products", "promotions", "digital_capabilities", "strengths", "weaknesses"]:
        if not isinstance(data.get(arr_key), list):
            data[arr_key] = []
    
    # Ensure interest_rates is dict
    if not isinstance(data.get("interest_rates"), dict):
        data["interest_rates"] = {}
    
    return data
