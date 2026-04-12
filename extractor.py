import os
import json
import re

# Lazy import - chỉ import khi cần
_groq_client = None

def get_groq_client():
    """Lazy initialization của Groq client"""
    global _groq_client
    
    if _groq_client is not None:
        return _groq_client
    
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        print("⚠️ GROQ_API_KEY_BK not set")
        return None
    
    try:
        # Thử import
        try:
            from groq import Groq
        except ImportError:
            print("❌ Cannot import groq")
            return None
        
        # Khởi tạo đơn giản nhất có thể
        _groq_client = Groq(api_key=api_key)
        return _groq_client
        
    except Exception as e:
        print(f"❌ Groq init error: {e}")
        return None

def clean_json(text):
    """Trích xuất JSON"""
    if not text:
        return None
    
    try:
        return json.loads(text)
    except:
        pass
    
    # Tìm JSON trong text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    
    return None

def extract_data(text, url):
    """Trích xuất dữ liệu ngân hàng"""
    
    client = get_groq_client()
    
    # Fallback nếu không có API
    if not client:
        domain = url.split("//")[-1].split("/")[0].replace("www.", "").upper()
        return {
            "url": url,
            "analysis": {
                "bank_name": domain,
                "bank_code": None,
                "products": [
                    {"category": "SAVINGS", "name": "Tiết kiệm", "features": []},
                    {"category": "LOAN", "name": "Cho vay", "features": []}
                ],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Demo mode - API not configured",
                "strengths": ["Digital banking"],
                "weaknesses": ["API key missing"]
            },
            "extraction_quality": "demo"
        }

    prompt = f"""Phân tích website ngân hàng.

URL: {url}
CONTENT: {text[:4000]}

Trả về JSON:
{{
    "bank_name": "Tên ngân hàng",
    "products": [{{"category": "SAVINGS", "name": "Tên SP"}}],
    "interest_rates": {{}},
    "promotions": [],
    "digital_capabilities": [],
    "positioning": "Mô tả",
    "strengths": [],
    "weaknesses": []
}}

JSON hợp lệ."""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Trả về JSON hợp lệ."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )

        content = res.choices[0].message.content.strip()
        parsed = clean_json(content)

        if not parsed:
            parsed = {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Parse error",
                "strengths": [],
                "weaknesses": []
            }

        # Normalize arrays
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
        print(f"❌ Extraction error: {e}")
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Error",
                "strengths": [],
                "weaknesses": [str(e)[:50]]
            },
            "extraction_quality": "error"
        }
