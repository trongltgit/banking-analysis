import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=1500, retries=3):
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
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
            
            if res.status_code == 429:
                wait_time = 3 ** attempt
                print(f"      ⏳ Strategy rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2)
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
    """Tạo chiến lược đơn giản hơn để tránh rate limit"""
    
    # Format data ngắn gọn - PYTHON SYNTAX (không phải JS)
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

    prompt = f"""Phân tích chiến lược ngắn gọn:

{banks_summary}

Trả về JSON:
{{
    "executive_summary": "Tóm tắt 2-3 câu",
    "competitive_ranking": [
        {{"rank": 1, "bank": "Tên", "position": "Leader", "score": "8/10", "key_strength": "Điểm mạnh"}}
    ],
    "strategic_recommendations": {{
        "overall_strategy": "Chiến lược tổng thể",
        "immediate_actions": ["Hành động 1", "Hành động 2"]
    }},
    "market_opportunities": [
        {{"opportunity": "Cơ hội", "priority": "Cao"}}
    ]
}}

JSON ngắn gọn."""

    try:
        content = call_groq_api(prompt, model="llama-3.1-8b-instant", max_tokens=1200)
        strategy = clean_json(content)
        
        if not strategy:
            raise Exception("Parse error")
            
        return strategy
        
    except Exception as e:
        print(f"      ❌ Strategy error: {str(e)[:80]}")
        
        # PYTHON SYNTAX ĐÚNG - dùng list comprehension
        ranking = []
        for i, b in enumerate(banks_summary):
            ranking.append({
                "rank": i + 1,
                "bank": b.get("name", "Unknown"),
                "position": "Unknown",
                "score": "-",
                "key_strength": "N/A"
            })
        
        return {
            "executive_summary": f"Error generating strategy: {str(e)[:50]}",
            "competitive_ranking": ranking,
            "strategic_recommendations": {
                "overall_strategy": "Retry with 2-3 banks maximum",
                "immediate_actions": ["Check API rate limits", "Retry in 1 minute"]
            },
            "market_opportunities": []
        }
