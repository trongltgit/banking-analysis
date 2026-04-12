from groq import Groq
import os
import json

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])

def extract_data(text, url):
    # Sử dụng Llama-3.3-70b để trích xuất dữ liệu cực kỳ chính xác
    model_id = "llama-3.3-70b-versatile"
    
    prompt = f"""
    Trích xuất thông tin tài chính từ nội dung website sau đây.
    Yêu cầu trả về DUY NHẤT một đối tượng JSON (không giải thích thêm).

    Cấu trúc JSON mong muốn:
    {{
      "bank_name": "Tên ngân hàng",
      "products": ["Sản phẩm 1", "Sản phẩm 2"],
      "interest_rates": "Thông tin lãi suất",
      "promotions": ["Ưu đãi 1", "Ưu đãi 2"]
    }}

    Nội dung:
    {text}
    """

    try:
        res = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, # Giảm nhiệt độ để trích xuất dữ liệu cứng, chính xác
            response_format={"type": "json_object"} # Ép buộc Groq trả về JSON
        )

        return {
            "url": url,
            "analysis": json.loads(res.choices[0].message.content)
        }

    except Exception as e:
        return {
            "url": url,
            "analysis": f"LLM error: {str(e)}"
        }
