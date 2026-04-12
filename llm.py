from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])

# 🔥 MODEL MỚI (ổn định hiện tại)
MODEL = "llama-3.1-70b-versatile"


def analyze_strategy(results):
    try:
        prompt = f"""
You are a senior banking strategy consultant.

Analyze competitor banks data:

{results}

Return STRICT JSON ONLY:
{{
  "insights": [
    "insight 1",
    "insight 2",
    "insight 3"
  ],
  "strength_leader": "bank name",
  "weakness_leader": "bank name",
  "recommendations": [
    "strategy 1",
    "strategy 2",
    "strategy 3"
  ]
}}
"""

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200
        )

        return res.choices[0].message.content

    except Exception as e:
        return {
            "error": str(e),
            "insights": [],
            "recommendations": []
        }
