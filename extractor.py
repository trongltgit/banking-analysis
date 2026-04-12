import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=2000, retries=3):
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
            {"role": "system", "content": "Bạn là chuyên gia phân tích ngân hàng Việt Nam. Trả về JSON hợp lệ, ngắn gọn, không giải thích thêm."},
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
                print(f"❌ 400 Bad Request: {res.text[:400]}")
                # Nếu vẫn lỗi model, fallback sang model nhỏ hơn
                if "decommissioned" in res.text or "not supported" in res.text:
                    print("🔄 Fallback to llama-3.1-8b-instant")
                    payload["model"] = "llama-3.1-8b-instant"
                    continue
                    
            if res.status_code == 429:
                wait = 8 * (attempt + 1)
                print(f"⏳ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
                
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"❌ API Error (attempt {attempt+1}): {str(e)}")
            if attempt < retries - 1:
                time.sleep(4)
                continue
            raise

    raise Exception("Max retries exceeded")


def extract_data(text, url):
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".vn", "").replace(".com", "").upper()
    
    content = text[:4000]   # Rút mạnh hơn để tránh lỗi

    prompt = f"""Phân tích website ngân hàng {domain}.
URL: {url}
CONTENT: {content}

Trả về đúng JSON sau, không thêm bất kỳ chữ nào khác:

{{
  "bank_name": "Tên ngân hàng",
  "bank_code": "TCB/BIDV/VTB/...",
  "products": [
    {{"category": "TIETKIEM", "name": "Tên SP", "features": ["đặc điểm"]}}
  ],
  "interest_rates": {{"savings": "5.5%"}},
  "promotions": [],
  "digital_capabilities": ["App", "Internet Banking"],
  "strategic_analysis": {{
    "positioning": "...",
    "target_segments": ["..."],
    "key_differentiators": ["..."],
    "pricing_strategy": "...",
    "distribution_strategy": "...",
    "marketing_strategy": "..."
  }},
  "competitive_assessment": {{
    "strengths": ["..."],
    "weaknesses": ["..."],
    "market_position": "Leader/Challenger/Follower",
    "competitive_threat_level": "High/Medium/Low"
  }}
}}

Chỉ trả JSON thuần."""

    try:
        # Dùng model mạnh trước
        ai_content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=1800)
        parsed = clean_json(ai_content)
        
        if not parsed:
            # Fallback model nhỏ, nhanh, rẻ
            ai_content = call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=1500)
            parsed = clean_json(ai_content)

        if not parsed:
            raise Exception("Cannot parse JSON from AI")

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


def clean_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except:
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
