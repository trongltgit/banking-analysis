from groq import Groq
import os

# 🔥 dùng đúng ENV của bạn
client = Groq(api_key=os.getenv("GROQ_API_KEY_BK"))


def extract_data(text, url):
    try:
        if not text or len(text.strip()) == 0:
            return {
                "url": url,
                "analysis": "No content"
            }

        # 🔥 LIMIT TEXT CỨNG
        text = text[:1000]

        prompt = f"""
        Phân tích nội dung website ngân hàng:

        - Tên ngân hàng
        - Sản phẩm chính
        - Lãi suất (nếu có)
        - Ưu đãi

        Nội dung:
        {text}

        Trả về JSON:
        {{
            "bank": "...",
            "products": "...",
            "interest": "...",
            "offers": "..."
        }}
        """

        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,   # 🔥 giảm mạnh
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
