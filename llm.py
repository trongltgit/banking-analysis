from groq import Groq
import os

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])


def analyze_strategy(results):
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""
                Phân tích chiến lược ngân hàng từ dữ liệu:

                {results}

                Trả về dạng dễ đọc:

                1. Điểm mạnh từng ngân hàng
                2. Điểm yếu
                3. Xu hướng digital
                4. Đề xuất chiến lược cạnh tranh

                Viết ngắn gọn, rõ ràng, dạng bullet point.
                """
            }],
            temperature=0.5,
            max_tokens=800
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"Strategy error: {str(e)}"
