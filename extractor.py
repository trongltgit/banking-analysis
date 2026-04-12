import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=2000, retries=3):
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
            {"role": "system", "content": "Bạn là chuyên gia phân tích ngân hàng Việt Nam. Trả về JSON hợp lệ, không giải thích thêm."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "top_p": 0.9
    }

    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=80)
            
            if res.status_code == 400:
                print(f"❌ 400 Bad Request: Prompt có thể quá dài hoặc lỗi format")
                print(f"Response: {res.text[:300]}")
                # Thử rút gọn prompt
                if attempt == 0:
                    prompt = prompt[:8000]  # Rút gọn
                    continue
                    
            if res.status_code == 429:
                wait = 6 * (attempt + 1)
                print(f"⏳ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
                
            if res.status_code >= 500:
                print(f"⚠️ Server error {res.status_code}, retry...")
                time.sleep(3)
                continue

            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(f"❌ API Error (attempt {attempt+1}): {str(e)}")
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise

    raise Exception("Max retries exceeded")


def clean_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except:
        # Tìm JSON trong markdown
        patterns = [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```', r'(\{.*\})']
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for m in matches:
                try:
                    cleaned = m.strip() if isinstance(m, str) else m[0].strip()
                    return json.loads(cleaned)
                except:
                    continue
    return None


def extract_data(text, url):
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".vn", "").replace(".com", "").upper()
    
    # Rút gọn content rất mạnh để tránh 400
    content = text[:4500] if len(text) > 4500 else text

    prompt = f"""Phân tích website ngân hàng {domain}.
URL: {url}
CONTENT: {content}

Trả về JSON theo đúng format sau, không thêm text nào khác:

{{
  "bank_name": "Tên ngân hàng đầy đủ",
  "bank_code": "TCB hoặc BIDV hoặc ...",
  "products": [
    {{"category": "TIETKIEM", "name": "Tên sản phẩm", "features": ["đặc điểm 1", "đặc điểm 2"]}}
  ],
  "interest_rates": {{"savings": "5.5-6.2%"}},
  "promotions": [{{"name": "Tên KM", "benefit": "Lợi ích"}}],
  "digital_capabilities": ["App tốt", "Internet Banking"],
  "strategic_analysis": {{
    "positioning": "Ngân hàng số hàng đầu / Ngân hàng truyền thống mạnh...",
    "target_segments": ["Học sinh sinh viên", "Doanh nghiệp nhỏ"],
    "key_differentiators": ["Lãi suất cao", "App đẹp"],
    "pricing_strategy": "Cạnh tranh",
    "distribution_strategy": "Online + Chi nhánh",
    "marketing_strategy": "Digital marketing mạnh"
  }},
  "competitive_assessment": {{
    "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
    "weaknesses": ["Điểm yếu 1"],
    "market_position": "Leader/Challenger/Follower",
    "competitive_threat_level": "High/Medium/Low"
  }}
}}

Chỉ trả về JSON thuần, không có ```json hay giải thích."""

    try:
        # Dùng model nhanh hơn trước
        content_ai = call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=2200, retries=3)
        parsed = clean_json(content_ai)
        
        if not parsed:
            # Thử model khác
            content_ai = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=2000, retries=2)
            parsed = clean_json(content_ai)

        if not parsed:
            raise Exception("Cannot parse AI response")

    except Exception as e:
        raise Exception(f"AI extraction failed: {str(e)}")

    # Normalize
    analysis = parsed
    analysis.setdefault("products", [])
    analysis.setdefault("promotions", [])
    analysis.setdefault("digital_capabilities", [])

    quality = "good" if len(analysis.get("products", [])) >= 5 else "limited"

    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }
