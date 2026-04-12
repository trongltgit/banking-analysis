from groq import Groq
import os

api_key = os.environ["GROQ_API_KEY_BK"]
client = Groq(api_key=api_key)


def analyze_strategy(results):
    try:
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{
                "role": "user",
                "content": f"""
                Phân tích chiến lược ngân hàng dựa trên dữ liệu:

                {results}

                Trả về:
                - Điểm mạnh
                - Điểm yếu
                - Xu hướng digital
                - Đề xuất cạnh tranh
                """
            }],
            temperature=0.5,
            max_tokens=1000
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"LLM analyze_strategy error: {str(e)}"
