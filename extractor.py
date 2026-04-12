from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_data(text, url):
    prompt = f"""
    Phân tích nội dung website ngân hàng sau và trích xuất:
    - Tên ngân hàng
    - Loại sản phẩm
    - Lãi suất (nếu có)
    - Ưu đãi chính

    Nội dung:
    {text[:3000]}

    Trả về dạng JSON ngắn gọn.
    """

    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
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
