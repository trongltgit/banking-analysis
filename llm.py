from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ.get("GROQ_API_KEY_BK", ""))

def clean_json(text):
    """Làm sạch JSON"""
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
    """Tạo chiến lược từ kết quả phân tích"""
    
    if not os.environ.get("GROQ_API_KEY_BK"):
        return {
            "executive_summary": "API key not configured. Strategy generation unavailable.",
            "strategic_recommendations": {"immediate_actions": []}
        }

    # Format competitor data
    competitors = []
    for r in results:
        a = r.get("analysis", {})
        competitors.append({
            "name": a.get("bank_name", "Unknown"),
            "products": len(a.get("products", [])),
            "promotions": len(a.get("promotions", [])),
            "digital": len(a.get("digital_capabilities", [])),
            "positioning": a.get("positioning", "Unknown")
        })

    prompt = f"""As a banking strategy consultant, analyze these competitors and provide strategic recommendations.

COMPETITORS:
{json.dumps(competitors, ensure_ascii=False, indent=2)}

Return JSON format:
{{
    "executive_summary": "2-3 sentence strategic summary",
    "competitive_landscape": {{
        "market_leader": "Which bank leads and why",
        "key_differentiators": ["Factor 1", "Factor 2"]
    }},
    "market_gaps": ["Opportunity 1", "Opportunity 2"],
    "strategic_recommendations": {{
        "immediate_actions": [
            {{"action": "Specific action", "rationale": "Why", "timeline": "0-6 months"}}
        ],
        "product_strategy": ["Strategy 1"],
        "digital_strategy": ["Strategy 1"]
    }},
    "competitor_analysis": [
        {{"bank": "Name", "position": "Leader/Challenger", "threat_level": "High/Medium/Low"}}
    ]
}}

Valid JSON only. No markdown."""

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
                "executive_summary": "Could not generate structured strategy. Raw analysis available.",
                "raw_response": content[:500],
                "competitive_landscape": {"market_leader": "Analysis pending"},
                "strategic_recommendations": {
                    "immediate_actions": [{"action": "Retry analysis", "rationale": "Parsing failed"}]
                }
            }

        return strategy

    except Exception as e:
        return {
            "executive_summary": f"Strategy generation error: {str(e)[:100]}",
            "competitive_landscape": {"market_leader": "Unknown"},
            "strategic_recommendations": {
                "immediate_actions": [{"action": "Check API configuration", "rationale": "Service error"}]
            },
            "error": str(e)[:100]
        }
