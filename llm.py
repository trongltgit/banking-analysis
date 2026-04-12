from groq import Groq
import os

api_key = os.environ["GROQ_API_KEY_BK"]
client = Groq(api_key=api_key)

def analyze_strategy(all_results):
    """
    all_results: Danh sách các dữ liệu đã trích xuất từ nhiều ngân hàng
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "system",
                "content": "Bạn là chuyên gia phân tích chiến lược tài chính cao cấp."
            }, {
                "role": "user",
                "content": f"""
                Dưới đây là dữ liệu so sánh từ nhiều ngân hàng/đối thủ:
                {all_results}

                Hãy thực hiện:
                1. So sánh đối đầu các chỉ số (Lãi suất, ưu đãi).
                2. Phân tích Điểm mạnh/Điểm yếu của từng bên.
                3. Nhận diện Xu hướng Digital chung của nhóm này.
                4. Đưa ra 03 chiến lược cụ thể để người dùng có thể cạnh tranh hoặc chiếm ưu thế.
                """
            }],
            temperature=0.7, # Tăng nhẹ để có các đề xuất chiến lược sáng tạo hơn
            max_tokens=2000
        )

        return res.choices[0].message.content

    except Exception as e:
        return f"LLM analyze_strategy error: {str(e)}"
