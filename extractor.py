from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])


def safe_json_parse(text):
    """
    Cố gắng parse JSON từ output LLM
    """
    try:
        return json.loads(text)
    except:
        # tìm JSON trong text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


def fallback_data(url):
    return {
        "bank_name": url,
        "products": ["Tiết kiệm", "Cho vay", "Ngân hàng số"],
        "interest_rates": "N/A",
        "promotions": ["Ưu đãi khách hàng mới"]
    }


def build_score(products):
    """
    Tạo score để vẽ chart
    """
    return {
        "digital": 9 if "Ngân hàng số" in products else 5,
        "loan": 8 if "Cho vay" in products else 5,
        "card": 7 if "Thẻ tín dụng" in products else 4,
        "saving": 8 if "Tiết kiệm" in products else 5
    }


def extract_data(text, url):
    prompt = f"""
Bạn là chuyên gia phân tích ngân hàng.

Nội dung:
{text}

YÊU CẦU (STRICT):
- Trả về JSON hợp lệ 100%
- KHÔNG giải thích
- LUÔN có ít nhất 3 sản phẩm

Danh mục sản phẩm hợp lệ:
["Tiết kiệm", "Cho vay", "Thẻ tín dụng", "Ngân hàng số", "Bảo hiểm"]

FORMAT:
{{
  "bank_name": "...",
  "products": ["...", "...", "..."],
  "interest_rates": "...",
  "promotions": ["...", "..."]
}}
"""

    try:
        res = client.chat.completions.create(
            model="mixtral-8x7b-32768",  # 🔥 model ổn định
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400
        )

        content = res.choices[0].message.content.strip()

        parsed = safe_json_parse(content)

        if not parsed:
            parsed = fallback_data(url)

        # 🔥 đảm bảo đủ fields
        parsed.setdefault("bank_name", url)
        parsed.setdefault("products", ["Tiết kiệm", "Cho vay", "Ngân hàng số"])
        parsed.setdefault("interest_rates", "N/A")
        parsed.setdefault("promotions", [])

        # 🔥 ép tối thiểu 3 products
        if len(parsed["products"]) < 3:
            parsed["products"] = list(set(parsed["products"] + ["Tiết kiệm", "Cho vay", "Ngân hàng số"]))[:3]

        # 🔥 thêm score cho dashboard
        parsed["score"] = build_score(parsed["products"])

        return {
            "url": url,
            "analysis": parsed
        }

    except Exception as e:
        fallback = fallback_data(url)
        fallback["error"] = str(e)
        fallback["score"] = build_score(fallback["products"])

        return {
            "url": url,
            "analysis": fallback
        }
