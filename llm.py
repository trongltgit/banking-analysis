import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def analyze_strategy(results):
    if not results or len(results) == 0:
        return {
            "error": "KẾT QUẢ TRỐNG - Không có dữ liệu ngân hàng nào để phân tích!"
        }

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=1500, retries=3):
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }

    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=70)
            
            if res.status_code == 429:
                wait = 7 * (attempt + 1)
                print(f"⏳ Strategy rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
                
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise
    raise Exception("Strategy API failed")


def analyze_strategy(results):
    # Rút gọn dữ liệu đầu vào
    summary = []
    for r in results:
        a = r.get("analysis", {})
        summary.append({
            "bank": a.get("bank_name", "Unknown"),
            "products": len(a.get("products", [])),
            "position": a.get("strategic_analysis", {}).get("positioning", "")[:60],
            "strengths": a.get("competitive_assessment", {}).get("strengths", [])[:2]
        })

    prompt = f"""Phân tích ngắn gọn 4 ngân hàng sau và đưa ra chiến lược:

{json.dumps(summary, ensure_ascii=False, indent=2)}

Trả về JSON đúng format sau:

{{
  "executive_summary": "Tóm tắt cạnh tranh thị trường ngân hàng số Việt Nam...",
  "competitive_ranking": [
    {{"rank": 1, "bank": "Tên ngân hàng", "position": "Leader", "score": "8.5/10", "key_strength": "..."}}
  ],
  "strategic_recommendations": {{
    "overall_strategy": "...",
    "product_strategy": "...",
    "immediate_actions": ["Hành động 1", "Hành động 2"]
  }}
}}"""

    try:
        content = call_groq_api(prompt, max_tokens=1400, retries=2)
        strategy = json.loads(content) if isinstance(content, str) else content
        
        if not isinstance(strategy, dict):
            raise Exception("Not a dict")
        return strategy
    except:
        # Fallback
        return {
            "executive_summary": "Strategy generation failed. Individual bank data is still available.",
            "competitive_ranking": [],
            "strategic_recommendations": {
                "overall_strategy": "Retry later",
                "product_strategy": "Compare products manually",
                "immediate_actions": ["Check individual bank results"]
            }
        }
