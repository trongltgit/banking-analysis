import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=2000, retries=3):
    """Gọi API"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
            
            if res.status_code == 429:
                wait_time = 5 * (attempt + 1)
                print(f"      ⏳ Strategy rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise
    
    raise Exception("Max retries exceeded")

def clean_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

def analyze_strategy(results):
    """Tạo chiến lược đơn giản hơn"""
    
    # Format data ngắn gọn
    banks_summary = []
    for r in results:
        a = r.get("analysis", {})
        strategic = a.get("strategic_analysis", {})
        competitive = a.get("competitive_assessment", {})
        
        banks_summary.append({
            "name": a.get("bank_name", "Unknown"),
            "products": len(a.get("products", [])),
            "positioning": strategic.get("positioning", "Unknown")[:50],
            "strengths": (competitive.get("strengths", []))[:2],
            "market_position": competitive.get("market_position", "Unknown")
        })

    # Prompt ngắn gọn
    prompt = f"""Phân tích chiến lược ngắn gọn:

{banks_summary}

Trả về JSON:
{{
    "executive_summary": "Tóm tắt 2-3 câu về cạnh tranh và chiến lược",
    "competitive_ranking": [
        {{"rank": 1, "bank": "Tên", "position": "Leader", "score": "8/10", "key_strength": "Điểm mạnh chính", "analysis": "Lý do xếp hạng"}}
    ],
    "strategic_recommendations": {{
        "overall_strategy": "Chiến lược tổng thể đề xuất",
        "product_strategy": "Chiến lược sản phẩm",
        "immediate_actions": ["Hành động 1", "Hành động 2"]
    }},
    "market_opportunities": [
        {{"opportunity": "Cơ hội", "rationale": "Lý do", "priority": "Cao"}}
    ]
}}

JSON hợp lệ, không markdown."""

    try:
        content = call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=1500, retries=2)
        strategy = clean_json(content)
        
        if not strategy:
            raise Exception("Parse error")
            
        return strategy
        
    except Exception as e:
        # Tạo strategy cơ bản nếu AI fail
        ranking = []
        for i, b in enumerate(banks_summary):
            ranking.append({
                "rank": i + 1,
                "bank": b.get("name", "Unknown"),
                "position": b.get("market_position", "Unknown"),
                "score": f"{min(b.get('products', 0), 10)}/10",
                "key_strength": (b.get("strengths") or ["N/A"])[0],
                "analysis": "Based on product count and positioning"
            })
        
        return {
            "executive_summary": f"Strategy AI error: {str(e)[:50]}. Using basic competitive analysis.",
            "competitive_ranking": ranking,
            "strategic_recommendations": {
                "overall_strategy": "Review individual bank analyses for detailed strategy",
                "product_strategy": "Compare product portfolios",
                "immediate_actions": ["Analyze gaps in product offerings", "Review digital capabilities"]
            },
            "market_opportunities": []
        }
