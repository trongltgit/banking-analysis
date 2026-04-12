from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY_BK"))

def analyze_strategy(data):
    prompt = f"""
    Dữ liệu từ nhiều ngân hàng:
    {data}

    Hãy:
    1. So sánh sản phẩm
    2. Phân tích điểm mạnh yếu
    3. Đưa ra chiến lược cạnh tranh cụ thể
    """

    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content
    except Exception as e:
        return f"Strategy error: {str(e)}"
