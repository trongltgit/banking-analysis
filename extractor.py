from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])


def extract_data(text, url):
    prompt = f"""
    Phân tích nội dung website ngân hàng:

    - Tên ngân hàng
    - Sản phẩm
    - Lãi suất
    - Ưu đãi

    Nội dung:
    {text}

    Trả về JSON:
    """

    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
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
