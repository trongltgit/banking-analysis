import os
import json
import re

# Import giống extractor
try:
    from groq import Groq
except ImportError:
    from groq import Client as Groq

def get_groq_client():
    """Khởi tạo Groq client"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        return None
    
    try:
        return Groq(api_key=api_key)
    except TypeError:
        import httpx
        http_client = httpx.Client(follow_redirects=True)
        return Groq(api_key=api_key, http_client=http_client)
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
    """Tạo chiến lược với Groq"""
    
    client = get_groq_client()
    if not client:
        return {
            "executive_summary": "Groq API not available. Using fallback analysis.",
            "strategic_recommendations": {"immediate_actions": []}
        }

    # Format data
    competitors = []
    for r in results:
        a = r.get("analysis", {})
        competitors.append({
            "name": a.get("bank_name", "Unknown"),
            "products": len(a.get("products", [])),
            "promotions": len(a.get("promotions", [])),
            "digital": len(a.get("digital_capabilities", []))
        })

    prompt = f"""Phân tích chiến lược cạnh tranh ngân hàng.

ĐỐI THỦ:
{json.dumps(competitors, ensure_ascii=False, indent=2)}

Trả về JSON:
{{
    "executive_summary": "Tóm tắt chiến lược 2-3 câu",
    "competitive_landscape": {{
        "market_leader": "Ngân hàng dẫn đầu và lý do",
        "key_differentiators": ["Yếu tố khác biệt"]
    }},
    "market_gaps": ["Cơ hội 1", "Cơ hội 2"],
    "strategic_recommendations": {{
        "immediate_actions": [
            {{"action": "Hành động cụ thể", "rationale": "Lý do", "timeline": "0-6 tháng"}}
        ]
    }}
}}

JSON hợp lệ, không markdown."""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )

        content = res.choices[0].message.content.strip()
        strategy = clean_json(content)

        if not strategy:
            return {
                "executive_summary": "Could not parse strategy. Raw data available.",
                "raw_response": content[:500],
                "strategic_recommendations": {"immediate_actions": []}
            }

        return strategy

    except Exception as e:
        return {
            "executive_summary": f"Strategy error: {str(e)[:100]}",
            "strategic_recommendations": {
                "immediate_actions": [{"action": "Check API", "rationale": "Error occurred"}]
            }
        }
