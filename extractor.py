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
                print(f"❌ 400 Bad Request: {res.text[:400]}")
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
    """Phân tích dữ liệu từ content crawl được"""
    
    # Xác định ngân hàng từ URL
    domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace(".vn", "").replace(".com", "")
    
    bank_mapping = {
        'techcombank': {'name': 'Techcombank', 'code': 'TCB'},
        'bidv': {'name': 'BIDV', 'code': 'BIDV'},
        'vietinbank': {'name': 'VietinBank', 'code': 'CTG'},
        'vietcombank': {'name': 'Vietcombank', 'code': 'VCB'},
        'agribank': {'name': 'Agribank', 'code': 'AGR'},
        'acb': {'name': 'ACB', 'code': 'ACB'},
        'sacombank': {'name': 'Sacombank', 'code': 'STB'},
        'vpbank': {'name': 'VPBank', 'code': 'VPB'},
        'mbbank': {'name': 'MB Bank', 'code': 'MBB'},
        'tpbank': {'name': 'TPBank', 'code': 'TPB'},
    }
    
    bank_info = bank_mapping.get(domain.lower(), {'name': domain.upper(), 'code': 'UNKNOWN'})
    
    # Kiểm tra nếu crawl lỗi
    if text.startswith("ERROR_CRAWL") or len(text) < 100:
        return {
            "url": url,
            "analysis": {
                "bank_name": bank_info['name'],
                "bank_code": bank_info['code'],
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "strategic_analysis": {
                    "positioning": "Không thể truy cập website",
                    "target_segments": [],
                    "key_differentiators": [],
                    "pricing_strategy": "Unknown",
                    "distribution_strategy": "Unknown",
                    "marketing_strategy": "Unknown"
                },
                "competitive_assessment": {
                    "strengths": [],
                    "weaknesses": ["Website không khả dụng hoặc chặn bot"],
                    "market_position": "Unknown",
                    "competitive_threat_level": "Unknown"
                }
            },
            "extraction_quality": "error"
        }

    # Cắt content để không quá dài
    content = text[:6000]

    prompt = f"""Phân tích website ngân hàng {bank_info['name']} ({bank_info['code']}).
URL: {url}

NỘI DUNG TRANG WEB:
{content}

Dựa trên nội dung thực tế từ website trên, trả về JSON chính xác:

{{
  "bank_name": "{bank_info['name']}",
  "bank_code": "{bank_info['code']}",
  "products": [
    {{"category": "SAVINGS", "name": "Tên sản phẩm cụ thể", "features": ["đặc điểm 1", "đặc điểm 2"]}}
  ],
  "interest_rates": {{"savings": "5.5%", "loan": "7.2%"}},
  "promotions": [
    {{"name": "Tên khuyến mãi", "benefit": "Lợi ích", "target_segment": "Đối tượng"}}
  ],
  "digital_capabilities": ["App mobile", "Internet banking", "Smart OTP"],
  "strategic_analysis": {{
    "positioning": "Định vị thị trường dựa trên nội dung web",
    "target_segments": ["Phân khúc KH 1", "Phân khúc KH 2"],
    "key_differentiators": ["Điểm khác biệt 1", "Điểm khác biệt 2"],
    "pricing_strategy": "Chiến lược giá",
    "distribution_strategy": "Chiến lược phân phối",
    "marketing_strategy": "Chiến lược marketing"
  }},
  "competitive_assessment": {{
    "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
    "weaknesses": ["Điểm yếu 1"],
    "market_position": "Leader/Challenger/Follower/Niche",
    "competitive_threat_level": "High/Medium/Low"
  }}
}}

QUAN TRỌNG: 
- Chỉ trả về JSON thuần, không thêm text khác
- Phân tích dựa trên NỘI DUNG THỰC TẾ từ website, không bịa đặt
- Nếu không tìm thấy thông tin, để giá trị rỗng [] hoặc "Unknown"
- Sản phẩm phải có tên cụ thể, không chung chung"""

    try:
        print(f"🤖 Calling AI for {bank_info['name']}...")
        ai_content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=1800)
        parsed = clean_json(ai_content)
        
        if not parsed:
            # Thử lại với model nhỏ hơn
            ai_content = call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=1500)
            parsed = clean_json(ai_content)

        if not parsed:
            raise Exception("Cannot parse JSON from AI")

    except Exception as e:
        print(f"❌ AI extraction failed for {bank_info['name']}: {str(e)}")
        # Trả về dữ liệu cơ bản nếu AI lỗi
        return {
            "url": url,
            "analysis": {
                "bank_name": bank_info['name'],
                "bank_code": bank_info['code'],
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "strategic_analysis": {
                    "positioning": f"{bank_info['name']} - Ngân hàng tại Việt Nam",
                    "target_segments": [],
                    "key_differentiators": [],
                    "pricing_strategy": "Unknown",
                    "distribution_strategy": "Unknown",
                    "marketing_strategy": "Unknown"
                },
                "competitive_assessment": {
                    "strengths": [],
                    "weaknesses": [f"Không thể phân tích chi tiết: {str(e)}"],
                    "market_position": "Unknown",
                    "competitive_threat_level": "Unknown"
                }
            },
            "extraction_quality": "error"
        }

    # Normalize và đánh giá chất lượng
    analysis = parsed
    
    # Đảm bảo các trường tồn tại
    analysis.setdefault("products", [])
    analysis.setdefault("promotions", [])
    analysis.setdefault("digital_capabilities", [])
    analysis.setdefault("interest_rates", {})
    analysis.setdefault("strategic_analysis", {})
    analysis.setdefault("competitive_assessment", {})
    
    # Đánh giá chất lượng
    quality = "deep" if len(analysis.get("products", [])) >= 5 else \
              "good" if len(analysis.get("products", [])) >= 2 else "limited"

    return {
        "url": url,
        "analysis": analysis,
        "extraction_quality": quality
    }


def clean_json(text):
    """Làm sạch và parse JSON từ AI response"""
    if not text:
        return None
    
    # Thử parse trực tiếp
    try:
        return json.loads(text.strip())
    except:
        pass
    
    # Tìm JSON trong markdown code block
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'\{[\s\S]*"bank_name"[\s\S]*\}'  # Tìm object có bank_name
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for m in matches:
            try:
                cleaned = m.strip() if isinstance(m, str) else m[0].strip()
                return json.loads(cleaned)
            except:
                continue
    
    # Thử tìm bất kỳ JSON object nào
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    
    return None
