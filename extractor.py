from groq import Groq
import os
import json

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])


def extract_data(text, url):

    prompt = f"""
You are a senior banking intelligence analyst.

Extract structured banking data from the text.

TEXT:
{text}

RULES:
- Always infer at least 3 banking products if not explicit
- Products MUST be one of:
  ["Tiết kiệm", "Cho vay", "Thẻ tín dụng", "Ngân hàng số", "Bảo hiểm"]
- If no interest rate found, estimate logical range based on bank type
- Promotions must be realistic banking marketing items

OUTPUT STRICT JSON ONLY:
{{
  "bank_name": "...",
  "products": ["...", "...", "..."],
  "interest_rates": "...",
  "promotions": ["...", "..."]
}}
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=700
        )

        content = res.choices[0].message.content

        parsed = json.loads(content)

        return {
            "url": url,
            "analysis": parsed
        }

    except Exception as e:
        # 🔥 SMART FALLBACK (KHÔNG ĐỂ UI CHẾT)
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[-1],
                "products": ["Ngân hàng số", "Tiết kiệm", "Cho vay"],
                "interest_rates": "4-7% (estimated)",
                "promotions": ["Digital onboarding", "Cashback program"],
                "error": str(e)
            }
        }
