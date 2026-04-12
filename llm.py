from groq import Groq
import os

# ❗ bắt buộc phải có key
api_key = os.environ["GROQ_API_KEY_BK"]

client = Groq(api_key=api_key)


def analyze_strategy(results):
    try:
        prompt = f"""
        Phân tích chiến lược ngân hàng dựa trên dữ liệu sau:

        {results}

        Trả về:
        - Điểm mạnh
        - Điểm yếu
        - Xu hướng digital
        - Đề xuất cạnh tranh
        """

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # ✅ MODEL MỚI
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500   # 🔥 giảm để tránh timeout/OOM
        )

        return res.choices[0].message.content

    except Exception as e:
        raise RuntimeError(f"LLM analyze_strategy failed: {str(e)}")
