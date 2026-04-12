from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY_BK"))

def extract_data(text, url):
    try:
        prompt = f"""
        Tóm tắt website ngân hàng:

        {text}

        Trả JSON:
        {{
            "bank": "...",
            "products": "...",
            "interest": "...",
            "offers": "..."
        }}
        """

        res = client.chat.completions.create(
            model="llama-3.3-8b-instant",   # ✅ FIX
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
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
