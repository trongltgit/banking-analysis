from groq import Groq
import os

# ❗ STRICT: bắt buộc phải có key
api_key = os.environ["GROQ_API_KEY_BK"]

client = Groq(api_key=api_key)


def analyze_strategy(results):
    try:
        res = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
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
            max_tokens=1200
        )

        return res.choices[0].message.content

    except Exception as e:
        raise RuntimeError(f"LLM analyze_strategy failed: {str(e)}")
