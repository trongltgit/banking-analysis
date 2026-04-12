from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY_BK"))

def extract_data(text, url):
    prompt = f"""
    Phân tích nội dung website ngân hàng sau và trích xuất thông tin:

    - Tên ngân hàng
    - Sản phẩm chính (tiền gửi, vay, thẻ...)
    - Lãi suất (nếu có)
    - Ưu đãi nổi bật

    Nội dung:
    {text[:3000]}

    Trả về JSON dạng:
    {{
        "bank": "...",
        "products": "...",
        "interest": "...",
        "offers": "..."
    }}
    """

    try:
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )

        return {
            "url": url,
            "analysis": res.choices[0].message.content
        }

    except Exception as e:
        return {
            "url": url,
            "analysis": f"LLM error: {str(e)}"
        }
