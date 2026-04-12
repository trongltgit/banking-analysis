from groq import Groq
import os
import json

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])


def extract_data(text, url):
    prompt = f"""
    Bạn là chuyên gia phân tích ngân hàng.

    Hãy trích xuất thông tin từ nội dung sau:

    {text}

    QUY TẮC:
    - LUÔN phải có ít nhất 3 sản phẩm
    - Nếu không rõ, suy luận hợp lý
    - Sản phẩm phải thuộc các nhóm:
      ["Tiết kiệm", "Cho vay", "Thẻ tín dụng", "Ngân hàng số", "Bảo hiểm"]

    Trả về JSON:
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
            temperature=0.3,
            max_tokens=500
        )

        content = res.choices[0].message.content

        try:
            parsed = json.loads(content)
        except:
            parsed = {
                "bank_name": url,
                "products": ["Tiết kiệm", "Cho vay", "Ngân hàng số"],
                "interest_rates": "",
                "promotions": []
            }

        return {
            "url": url,
            "analysis": parsed
        }

    except Exception as e:
        return {
            "url": url,
            "analysis": {
                "bank_name": url,
                "products": ["Tiết kiệm", "Cho vay", "Ngân hàng số"],
                "interest_rates": "",
                "promotions": [],
                "error": str(e)
            }
        }
