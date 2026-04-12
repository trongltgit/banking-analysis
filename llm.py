from groq import Groq
import os

# ✅ Validate API key
api_key = os.getenv("GROQ_API_KEY_BK")

if not api_key:
    raise ValueError("❌ Missing GROQ_API_KEY_BK in environment variables")

client = Groq(api_key=api_key)


# ===============================
# 1. Extract data from website
# ===============================
def extract_data(text, url):
    prompt = f"""
    Phân tích nội dung website ngân hàng sau và trích xuất thông tin:

    - Tên ngân hàng
    - Sản phẩm chính
    - Lãi suất
    - Ưu đãi

    Nội dung:
    {text[:3000]}

    Trả về JSON:
    {{
        "bank": "...",
        "products": "...",
        "interest": "...",
        "offers": "..."
    }}
    """

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # ✅ model mới
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
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


# ===============================
# 2. Analyze strategy (QUAN TRỌNG)
# ===============================
def analyze_strategy(results):
    try:
        prompt = f"""
        Dựa trên dữ liệu các ngân hàng sau:

        {results}

        Hãy phân tích:
        - Điểm mạnh chung
        - Điểm yếu
        - Xu hướng digital banking
        - Đề xuất chiến lược cạnh tranh
        """

        res = client.chat.completions.create(
            model="llama-3.1-70b-versatile",   # ✅ model mạnh hơn cho strategy
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1200
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"Strategy error: {str(e)}"
