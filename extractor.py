import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=3000, retries=3):
    """Gọi Groq API với rate limit handling"""
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
            {
                "role": "system", 
                "content": "Bạn là chuyên gia phân tích ngân hàng cấp cao. Trả về JSON hợp lệ."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)
            
            if res.status_code == 429:
                # Rate limit - đợi lâu hơn
                wait_time = 5 * (attempt + 1)  # 5, 10, 15 seconds
                print(f"      ⏳ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if res.status_code == 502 or res.status_code == 503:
                # Server error - retry
                print(f"      ⚠️ Server error {res.status_code}, retrying...")
                time.sleep(3)
                continue
            
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            print(f"      ⏱️ Timeout (attempt {attempt+1})")
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise Exception("Request timeout")
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise
    
    raise Exception("Max retries exceeded")

def clean_json(text):
    """Làm sạch JSON"""
    if not text:
        return None
    
    try:
        return json.loads(text)
    except:
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
    """Deep Learning Extraction"""
    
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".com", "").replace(".vn", "").upper()
    
    crawl_error = text.startswith("ERROR_CRAWL")
    
    # Rút gọn prompt để nhanh hơn
    prompt = f"""Phân tích website ngân hàng. Trả về JSON đầy đủ.

URL: {url}
CONTENT: {text[:6000]}

Yêu cầu phân tích:
1. Tên ngân hàng đầy đủ, mã CK
2. Danh mục sản phẩm đầy đủ (tối thiểu 8-12 sản phẩm): Tiết kiệm, Cho vay, Thẻ, Bảo hiểm, Đầu tư, Ngân hàng số
3. Lãi suất nếu có
4. Khuyến mãi nếu có  
5. Chiến lược: positioning, target segments, differentiators, pricing, distribution, marketing
6. Đánh giá cạnh tranh: strengths (3-5), weaknesses (2-3), market position, threat level

JSON format:
{{
    "bank_name": "...",
    "bank_code": "...",
    "products": [{{"category": "SAVINGS", "name": "...", "features": ["..."]}}],
    "interest_rates": {{"savings": "X%"}},
    "promotions": [{{"name": "...", "benefit": "..."}}],
    "digital_capabilities": ["..."],
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
        "market_position": "Leader/Challenger/Follower/Niche",
        "competitive_threat_level": "High/Medium/Low"
    }}
}}

Chỉ trả về JSON, không giải thích."""

    try:
        # Thử model nhỏ hơn trước cho nhanh
        content = call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=2500, retries=3)
        parsed = clean_json(content)
        
        if not parsed:
            # Retry với model khác
            content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=2500, retries=2)
            parsed = clean_json(content)
        
        if not parsed:
            raise Exception("Cannot parse AI response")
            
    except Exception as e:
        raise Exception(f"AI extraction failed: {str(e)}")

    # Normalize
    analysis = parsed
    
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
    
    for key in ["products", "promotions", "digital_capabilities"]:
        if not isinstance(analysis.get(key), list):
            analysis[key] = []
    
    quality = "good" if len(analysis.get("products", [])) >= 6 else "limited"
    
    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }
