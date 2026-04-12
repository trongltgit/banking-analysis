from groq import Groq
import os

api_key = os.environ["GROQ_API_KEY_BK"]

client = Groq(api_key=api_key)


def extract_data(text, url):
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"""
                Trích xuất thông tin ngân hàng từ nội dung:

                {text[:3000]}

                JSON:
                {{
                    "bank": "...",
                    "products": "...",
                    "interest": "...",
                    "offers": "..."
                }}
                """
            }],
            temperature=0.3,
            max_tokens=800
        )

        return {
            "url": url,
            "analysis": res.choices[0].message.content
        }

    except Exception as e:
        raise RuntimeError(f"LLM extract_data failed for {url}: {str(e)}")
