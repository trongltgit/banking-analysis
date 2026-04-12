from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ.get("GROQ_API_KEY_BK", ""))

def clean_json(text):
    """Trích xuất JSON từ text"""
    if not text:
        return None
    
    # Thử parse trực tiếp
    try:
        return json.loads(text)
    except:
        pass
    
    # Tìm JSON trong markdown code block
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
    """Trích xuất dữ liệu ngân hàng với AI"""
    
    # Kiểm tra API key
    if not os.environ.get("GROQ_API_KEY_BK"):
        return {
            "url": url,
            "analysis": {
                "bank_name": "API Key Missing",
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Configuration error",
                "strengths": [],
                "weaknesses": ["GROQ_API_KEY_BK not set"]
            },
            "extraction_quality": "error"
        }
    
    prompt = f"""Analyze this bank website content and extract structured data.

URL: {url}
CONTENT: {text[:6000]}

Extract ONLY factual information into this JSON format:
{{
    "bank_name": "Full bank name",
    "bank_code": "Stock code if mentioned (VCB, TCB, etc)",
    "products": [
        {{"category": "SAVINGS/LOAN/CARD/DIGITAL/INSURANCE/INVESTMENT", "name": "Product name", "features": ["feature1"]}}
    ],
    "interest_rates": {{"savings": "X%", "loan": "Y%"}},
    "promotions": [{{"name": " Promo name", "benefit": "Description"}}],
    "digital_capabilities": ["Mobile app", "Internet banking"],
    "positioning": "Bank's market positioning",
    "strengths": ["Strength 1"],
    "weaknesses": ["Weakness 1"]
}}

Rules:
- Only include data visible in the content
- Empty array [] if no data
- No made-up interest rates
- Valid JSON only, no markdown"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Model ổn định, nhanh
            messages=[
                {"role": "system", "content": "You extract banking data into valid JSON. No explanations, only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )

        content = res.choices[0].message.content.strip()
        parsed = clean_json(content)

        if not parsed:
            # Retry với prompt đơn giản hơn
            retry_prompt = f"""Fix this into valid JSON: {content}
Output ONLY JSON, no other text."""
            
            res2 = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": retry_prompt}],
                temperature=0,
                max_tokens=1000
            )
            parsed = clean_json(res2.choices[0].message.content.strip())

        if not parsed:
            parsed = {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "bank_code": None,
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Could not parse AI response",
                "strengths": [],
                "weaknesses": ["AI extraction failed"]
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
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                "bank_code": None,
                "products": [],
                "interest_rates": {},
                "promotions": [],
                "digital_capabilities": [],
                "positioning": "Extraction error",
                "strengths": [],
                "weaknesses": [str(e)[:100]]
            },
            "extraction_quality": "error",
            "error": str(e)[:100]
        }
