import os
import json
import re

# Fix: Import groq đúng cách cho version mới
try:
    from groq import Groq
except ImportError:
    from groq import Client as Groq

def get_groq_client():
    """Khởi tạo Groq client an toàn"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    
    if not api_key:
        print("⚠️ WARNING: GROQ_API_KEY_BK not set")
        return None
    
    try:
        # Thử cách 1: Standard initialization
        client = Groq(api_key=api_key)
        return client
    except TypeError as e:
        if "proxies" in str(e):
            # Fix: Khởi tạo không dùng proxies
            import httpx
            http_client = httpx.Client(follow_redirects=True)
            client = Groq(api_key=api_key, http_client=http_client)
            return client
        raise
    except Exception as e:
        print(f"❌ Groq client error: {e}")
        return None

def clean_json(text):
    """Trích xuất JSON từ text"""
    if not text:
        return None
    
    try:
        return json.loads(text)
    except:
        pass
    
    # Tìm JSON trong code blocks
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
    """Trích xuất dữ liệu ngân hàng với Groq AI"""
    
    client = get_groq_client()
    
    if not client:
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "bank_code": None,
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "API not configured",
                "strengths": [],
                "weaknesses": ["GROQ_API_KEY_BK not set or invalid"]
            },
            "extraction_quality": "error"
        }

    prompt = f"""Phân tích nội dung website ngân hàng và trích xuất dữ liệu có cấu trúc.

URL: {url}
NỘI DUNG: {text[:5000]}

Trích xuất thông tin vào JSON format:
{{
    "bank_name": "Tên ngân hàng đầy đủ",
    "bank_code": "Mã chứng khoán nếu có (VCB, TCB, BID...)",
    "products": [
        {{"category": "SAVINGS/LOAN/CARD/DIGITAL/INSURANCE", "name": "Tên sản phẩm", "features": ["đặc điểm"]}}
    ],
    "interest_rates": {{"savings": "X%/năm", "loan": "Y%/năm"}},
    "promotions": [{{"name": "Tên CTKM", "benefit": "Lợi ích"}}],
    "digital_capabilities": ["App mobile", "Internet banking"],
    "positioning": "Định vị thương hiệu",
    "strengths": ["Điểm mạnh 1"],
    "weaknesses": ["Điểm yếu 1"]
}}

Quy tắc:
- Chỉ dùng dữ liệu có thực từ nội dung
- Không bịa đặt lãi suất
- Trả về JSON hợp lệ, không markdown"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Trả về JSON hợp lệ. Không giải thích."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )

        content = res.choices[0].message.content.strip()
        parsed = clean_json(content)

        if not parsed:
            # Retry
            retry = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": f"Sửa thành JSON hợp lệ: {content}"}
                ],
                temperature=0,
                max_tokens=1000
            )
            parsed = clean_json(retry.choices[0].message.content.strip())

        if not parsed:
            parsed = {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "bank_code": None,
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Parse error",
                "strengths": [],
                "weaknesses": ["JSON parsing failed"]
            }

        # Normalize
        for key in ["products", "promotions", "digital_capabilities", "strengths", "weaknesses"]:
            if not isinstance(parsed.get(key), list):
                parsed[key] = []
        
        if not isinstance(parsed.get("interest_rates"), dict):
            parsed["interest_rates"] = {}

        return {
            "url": url,
            "analysis": parsed,
            "extraction_quality": "good" if len(parsed.get("products", [])) > 0 else "limited"
        }

    except Exception as e:
        print(f"❌ Extraction error for {url}: {e}")
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "bank_code": None,
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Error",
                "strengths": [],
                "weaknesses": [str(e)[:100]]
            },
            "extraction_quality": "error"
        }
