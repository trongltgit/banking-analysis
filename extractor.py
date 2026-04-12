from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])

MODEL = "llama-3.1-70b-versatile"


def extract_data(text, url):
    prompt = f"""
You are a banking data extraction engine.

Extract structured information from website text.

TEXT:
{text[:3000]}

Return STRICT JSON ONLY:
{{
  "bank_name": "string",
  "products": [
    {{"name": "string", "type": "Savings|Loan|Card|Digital|Insurance"}}
  ],
  "interest_rates": "string or range",
  "promotions": ["string"]
}}
"""

    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800
        )

        content = res.choices[0].message.content

        # 🔥 CLEAN JSON ROBUST
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise ValueError("Invalid JSON")

        return {
            "url": url,
            "analysis": parsed
        }

    except Exception:
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[1],
                "products": [],
                "interest_rates": "N/A",
                "promotions": []
            }
        }
