from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY_BK"))

def extract_data(text, url):
    try:
        # ❗ GIẢM SIZE TEXT (RẤT QUAN TRỌNG)
        text = text[:1500]

        prompt = f"""
        Tóm tắt nội dung ngân hàng:

        {text}

        Trả JSON:
        bank, products, interest, offers
        """

        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,   # ❗ giảm token
            timeout=10        # ❗ tránh treo
        )

        return {
            "url": url,
            "analysis": res.choices[0].message.content
        }

    except Exception as e:
        return {
            "url": url,
            "analysis": f"LLM ERROR: {str(e)}"
        }
