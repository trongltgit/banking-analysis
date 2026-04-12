from groq import Groq
import os
import json

api_key = os.environ["GROQ_API_KEY_BK"]
client = Groq(api_key=api_key)


def analyze_strategy(results):
    try:
        data_str = json.dumps(results, indent=2, ensure_ascii=False)

        prompt = f"""
Bạn là chuyên gia chiến lược ngân hàng.

Dữ liệu:
{data_str}

Phân tích:

1. Bank nào dẫn đầu từng mảng
2. Insight chiến lược
3. Điểm mạnh/yếu (có lý do)
4. Gap thị trường
5. 3 chiến lược cụ thể

Format:

## 🏆 Leader
## 🔍 Insight
## ⚖️ Strength/Weakness
## 🚨 Gap
## 🚀 Strategy
"""

        res = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"Strategy error: {str(e)}"
