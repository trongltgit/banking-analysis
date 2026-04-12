import os
import json
import re

_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        return None
    
    try:
        from groq import Groq
        _groq_client = Groq(api_key=api_key)
        return _groq_client
    except:
        return None

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
    client = get_groq_client()
    
    if not client:
        return {
            "executive_summary": "Demo mode - Add GROQ_API_KEY_BK for AI strategy",
            "competitive_landscape": {"market_leader": "API not configured"},
            "strategic_recommendations": {
                "immediate_actions": [
                    {"action": "Set GROQ_API_KEY_BK environment variable", "rationale": "Enable AI analysis"}
                ]
            }
        }

    competitors = []
    for r in results:
        a = r.get("analysis", {})
        competitors.append({
            "name": a.get("bank_name", "Unknown"),
            "products": len(a.get("products", []))
        })

    prompt = f"""Phân tích chiến lược ngân hàng.

Đối thủ: {json.dumps(competitors, ensure_ascii=False)}

Trả về JSON:
{{
    "executive_summary": "Tóm tắt chiến lược",
    "competitive_landscape": {{"market_leader": "Tên"}},
    "market_gaps": ["Cơ hội"],
    "strategic_recommendations": {{
        "immediate_actions": [{{"action": "Hành động", "rationale": "Lý do"}}]
    }}
}}"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )

        content = res.choices[0].message.content.strip()
        strategy = clean_json(content)

        if not strategy:
            return {
                "executive_summary": "Could not parse strategy",
                "strategic_recommendations": {"immediate_actions": []}
            }

        return strategy

    except Exception as e:
        return {
            "executive_summary": f"Error: {str(e)[:50]}",
            "strategic_recommendations": {"immediate_actions": []}
        }
