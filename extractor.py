from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])


def clean_json(text):
    """
    Cố gắng sửa JSON lỗi từ LLM
    """
    try:
        return json.loads(text)
    except:
        pass

    # extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            return None

    return None


def extract_data(text, url):

    prompt = f"""
You are a SENIOR BANKING INTELLIGENCE SYSTEM.

Your task:
Analyze real banking website content and extract ONLY factual + strongly implied data.

CRITICAL RULES:
- DO NOT invent random products
- ONLY infer when context strongly suggests it
- If uncertain, return empty array []
- DO NOT hallucinate interest rates
- Promotions must be explicitly or clearly implied
- Output must be VALID JSON ONLY (no markdown)

BANK PRODUCTS CLASSIFICATION:
- Tiết kiệm (Savings)
- Cho vay (Loans)
- Thẻ tín dụng (Credit cards)
- Ngân hàng số (Digital banking)
- Bảo hiểm (Insurance)

INPUT:
URL: {url}
TEXT:
{text}

OUTPUT FORMAT:
{{
  "bank_name": "string",
  "products": ["..."],
  "interest_rates": "string or empty",
  "promotions": ["..."]
}}
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON. No explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )

        content = res.choices[0].message.content.strip()

        parsed = clean_json(content)

        # ---- SECOND ATTEMPT (VERY IMPORTANT) ----
        if not parsed:
            repair_prompt = f"""
Fix this into VALID JSON ONLY:

{content}

Rules:
- Output only JSON
- No text
"""

            res2 = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": repair_prompt}],
                temperature=0,
                max_tokens=500
            )

            parsed = clean_json(res2.choices[0].message.content.strip())

        # ---- FINAL GUARANTEE (NO FAKE DATA, ONLY STRUCTURE) ----
        if not parsed:
            parsed = {
                "bank_name": url.split("//")[-1],
                "products": [],
                "interest_rates": "",
                "promotions": []
            }

        # normalize
        parsed["products"] = parsed.get("products") or []
        parsed["promotions"] = parsed.get("promotions") or []

        return {
            "url": url,
            "analysis": parsed
        }

    except Exception as e:
        # KHÔNG BỊ CRASH SYSTEM
        return {
            "url": url,
            "analysis": {
                "bank_name": url.split("//")[-1],
                "products": [],
                "interest_rates": "",
                "promotions": [],
                "error": str(e)
            }
        }
