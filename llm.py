import os
import json
import re
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000):
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Bạn là chiến lược gia ngân hàng hàng đầu. Trả về JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }
    
    res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    res.raise_for_status()
    data = res.json()
    return data["choices"][0]["message"]["content"]

def clean_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

def analyze_strategy(results):
    """Phân tích chiến lược so sánh toàn diện"""
    
    # Format dữ liệu chi tiết từng ngân hàng
    banks_data = []
    for r in results:
        a = r.get("analysis", {})
        strategic = a.get("strategic_analysis", {})
        competitive = a.get("competitive_assessment", {})
        
        banks_data.append({
            "name": a.get("bank_name", "Unknown"),
            "product_count": len(a.get("products", [])),
            "categories": list(set([p.get("category") for p in a.get("products", []) if isinstance(p, dict)])),
            "positioning": strategic.get("positioning", "Unknown"),
            "target_segments": strategic.get("target_segments", []),
            "key_differentiators": strategic.get("key_differentiators", []),
            "strengths": competitive.get("strengths", []),
            "weaknesses": competitive.get("weaknesses", []),
            "market_position": competitive.get("market_position", "Unknown"),
            "threat_level": competitive.get("competitive_threat_level", "Unknown"),
            "digital_score": len(a.get("digital_capabilities", [])),
            "promo_count": len(a.get("promotions", []))
        })

    prompt = f"""PHÂN TÍCH CHIẾN LƯỢC CẠNH TRANH NGÂN HÀNG - DEEP STRATEGIC ANALYSIS

Bạn là Senior Partner tại McKinsey, chuyên tư vấn chiến lược ngân hàng.

DỮ LIỆU ĐỐI THỦ:
{json.dumps(banks_data, ensure_ascii=False, indent=2)}

YÊU CẦU PHÂN TÍCH CHIẾN LƯỢC:

1. BẢNG XẾP HẠNG CẠNH TRANH:
   - Xác định rõ Leader, Challengers, Followers, Niche players
   - Lý do xếp hạng dựa trên dữ liệu

2. PHÂN TÍCH TỪNG ĐỐI THỦ CHI TIẾT:
   - Vị thế thị trường
   - Chiến lược sản phẩm
   - Chiến lược giá
   - Chiến lược phân phối
   - Điểm mạnh/yếu so sánh

3. SO SÁNH SẢN PHẨM:
   - Product matrix so sánh từng hạng mục
   - Gaps và overlaps
   - Best practices từng ngân hàng

4. CHIẾN LƯỢC KINH DOANH ĐỀ XUẤT:
   - Chiến lược tổng thể (Differentiation/Cost Leadership/Focus)
   - Chiến lược sản phẩm cụ thể
   - Chiến lược giá
   - Chiến lược kênh phân phối
   - Chiến lược marketing
   - Lộ trình thực thi 6-12-18 tháng

5. CƠ HỘI THỊ TRƯỜNG:
   - Phân khúc chưa khai thác
   - Sản phẩm còn thiếu
   - Xu hướng cần bắt kịp

OUTPUT JSON:
{{
    "executive_summary": "Tóm tắt chiến lược 3-4 câu cho CEO",
    "competitive_ranking": [
        {{
            "rank": 1,
            "bank": "Tên",
            "position": "Leader/Challenger/Follower/Niche",
            "score": "Điểm tổng quan",
            "key_strength": "Điểm mạnh quyết định"
        }}
    ],
    "detailed_competitor_analysis": [
        {{
            "bank": "Tên ngân hàng",
            "market_position": "Mô tả vị thế",
            "product_strategy": "Chiến lược sản phẩm",
            "pricing_strategy": "Chiến lược giá",
            "distribution_strategy": "Chiến lược phân phối",
            "digital_strategy": "Chiến lược số",
            "competitive_score": {{
                "product_breadth": "1-10",
                "digital_capability": "1-10",
                "pricing_competitiveness": "1-10",
                "brand_strength": "1-10",
                "overall": "1-10"
            }},
            "key_threats": ["Mối đe dọa 1"],
            "key_opportunities": ["Cơ hội 1"]
        }}
    ],
    "product_comparison_matrix": {{
        "savings_products": {{"leader": "Ngân hàng", "gap_analysis": "Nhận xét"}},
        "loan_products": {{"leader": "Ngân hàng", "gap_analysis": "Nhận xét"}},
        "digital_products": {{"leader": "Ngân hàng", "gap_analysis": "Nhận xét"}}
    }},
    "strategic_recommendations": {{
        "overall_strategy": "Chiến lược tổng thể đề xuất",
        "product_strategy": "Chiến lược sản phẩm cụ thể",
        "pricing_strategy": "Định vị giá đề xuất",
        "distribution_strategy": "Mở rộng kênh đề xuất",
        "digital_strategy": "Chuyển đổi số đề xuất",
        "implementation_roadmap": [
            {{
                "phase": "Giai đoạn 1 (0-6 tháng)",
                "actions": ["Hành động 1", "Hành động 2"],
                "milestones": "KPI đạt được",
                "investment_required": "Mức đầu tư"
            }},
            {{
                "phase": "Giai đoạn 2 (6-12 tháng)",
                "actions": ["Hành động 1"],
                "milestones": "KPI",
                "investment_required": "Mức đầu tư"
            }},
            {{
                "phase": "Giai đoạn 3 (12-18 tháng)",
                "actions": ["Hành động 1"],
                "milestones": "KPI",
                "investment_required": "Mức đầu tư"
            }}
        ]
    }},
    "market_opportunities": [
        {{
            "opportunity": "Cơ hội thị trường",
            "rationale": "Lý do",
            "potential_revenue": "Doanh thu tiềm năng",
            "difficulty": "Dễ/Trung bình/Khó",
            "priority": "Cao/Trung bình/Thấp"
        }}
    ],
    "risk_mitigation": ["Rủi ro và cách giảm thiểu"]
}}"""

    try:
        content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000)
        strategy = clean_json(content)
        
        if not strategy:
            raise Exception("Cannot parse strategy")
            
        return strategy
        
    except Exception as e:
        print(f"❌ Strategy generation failed: {e}")
        # Return meaningful fallback
        return {
            "executive_summary": "Phân tích chiến lược đang gặp lỗi kỹ thuật. Vui lòng thử lại.",
            "competitive_ranking": [{"rank": i+1, "bank": b.get("name"), "position": "Unknown"} for i, b in enumerate(banks_data)],
            "detailed_competitor_analysis": [],
            "strategic_recommendations": {
                "overall_strategy": "Error in generation",
                "implementation_roadmap": []
            },
            "error": str(e)
        }
