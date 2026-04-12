import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=2000, retries=3):
    """Gọi API với rate limit handling"""
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
            {"role": "system", "content": "Bạn là chuyên gia phân tích ngân hàng. Trả về JSON hợp lệ."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
            
            # Handle rate limit
            if res.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                print(f"      ⏳ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            raise Exception(f"Groq API error: {str(e)}")
    
    raise Exception("Max retries exceeded for Groq API")

def clean_json(text):
    """Làm sạch JSON"""
    if not text:
        return None
    
    try:
        return json.loads(text)
    except:
        # Tìm JSON trong text
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
    """Trích xuất với error handling tốt hơn"""
    
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".com", "").replace(".vn", "").upper()
    
    # Kiểm tra nếu crawl lỗi
    if text.startswith("ERROR_CRAWL"):
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
                    "positioning": "Cannot access website",
                    "target_segments": [],
                    "key_differentiators": [],
                    "pricing_strategy": "Unknown",
                    "distribution_strategy": "Unknown",
                    "marketing_strategy": "Unknown"
                },
                "competitive_assessment": {
                    "strengths": [],
                    "weaknesses": ["Website crawl failed"],
                    "market_position": "Unknown",
                    "competitive_threat_level": "Unknown"
                },
                "product_gaps_vs_market": []
            },
            "extraction_quality": "error",
            "error": text
        }

    # Rút gọn prompt để tránh rate limit
    prompt = f"""Phân tích website ngân hàng và trả về JSON.

URL: {url}
CONTENT: {text[:5000]}

Trả về JSON với cấu trúc:
{{
    "bank_name": "Tên đầy đủ",
    "bank_code": "Mã CK",
    "products": [
        {{"category": "SAVINGS/LOAN/CARD/DIGITAL/INSURANCE/INVESTMENT", "name": "Tên SP", "features": ["đặc điểm"]}}
    ],
    "interest_rates": {{"savings": "X%", "loan": "Y%"}},
    "promotions": [{{"name": "Tên CTKM", "benefit": "Lợi ích"}}],
    "digital_capabilities": ["Tính năng"],
    "strategic_analysis": {{
        "positioning": "Định vị",
        "target_segments": ["Phân khúc"],
        "key_differentiators": ["Điểm khác biệt"],
        "pricing_strategy": "Chiến lược giá",
        "distribution_strategy": "Kênh phân phối",
        "marketing_strategy": "Marketing"
    }},
    "competitive_assessment": {{
        "strengths": ["Điểm mạnh"],
        "weaknesses": ["Điểm yếu"],
        "market_position": "Leader/Challenger/Follower",
        "competitive_threat_level": "High/Medium/Low"
    }}
}}

Chỉ trả về JSON, không giải thích."""

    try:
        # Thử model nhỏ hơn trước để tránh rate limit
        content = call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=1500, retries=3)
        parsed = clean_json(content)
        
        if not parsed:
            raise Exception("Cannot parse AI response")
            
    except Exception as e:
        print(f"      ❌ AI error: {str(e)[:80]}")
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
                    "positioning": f"AI Error: {str(e)[:50]}",
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

    # Normalize
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
    for key in ["products", "promotions", "digital_capabilities"]:
        if not isinstance(analysis.get(key), list):
            analysis[key] = []
    
    quality = "good" if len(analysis.get("products", [])) >= 4 else "limited"
    
    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }
