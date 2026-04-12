from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY_BK"))

def extract_data(text, url):
    try:
        prompt = f"""
        Tóm tắt nhanh website ngân hàng:

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
            model="llama3-8b-8192",   # nhẹ nhất
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300   # 🔥 giảm mạnh
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
