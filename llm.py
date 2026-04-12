import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000, retries=3):
    """Gọi Groq API"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
            
            if res.status_code == 429:
                wait_time = 2 ** (attempt + 2)  # 4, 8, 16 seconds
                print(f"      ⏳ Strategy rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            res.raise_for_status()
            data = res.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise
    
    raise Exception("Max retries exceeded for strategy generation")

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
    """Deep Strategic Analysis - Phân tích chiến lược thực sự"""
    
    # Format dữ liệu chi tiết từng ngân hàng
    banks_data = []
    for r in results:
        a = r.get("analysis", {})
        strategic = a.get("strategic_analysis", {})
        competitive = a.get("competitive_assessment", {})
        
        # Tính điểm tổng quan
        product_score = min(len(a.get("products", [])) * 0.5, 10)
        digital_score = min(len(a.get("digital_capabilities", [])) * 1.5, 10)
        promo_score = min(len(a.get("promotions", [])) * 1, 5)
        overall_score = min(product_score + digital_score + promo_score, 10)
        
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
            "promo_count": len(a.get("promotions", [])),
            "calculated_score": round(overall_score, 1)
        })

    prompt = f"""PHÂN TÍCH CHIẾN LƯỢC CẠNH TRANH NGÂN HÀNG - DEEP STRATEGIC ANALYSIS

Bạn là Senior Partner tại McKinsey, chuyên tư vấn chiến lược ngân hàng.

DỮ LIỆU ĐỐI THỦ:
{json.dumps(banks_data, ensure_ascii=False, indent=2)}

YÊU CẦU PHÂN TÍCH CHIẾN LƯỢC CHUYÊN SÂU:

1. BẢNG XẾP HẠNG CẠNH TRANH:
   - Xếp hạng dựa trên: số lượng sản phẩm, khả năng số hóa, ưu đãi, định vị
   - Phân tích lý do xếp hạng chi tiết

2. PHÂN TÍCH CHI TIẾT TỪNG ĐỐI THỦ:
   - Vị thế thị trường và lý do
   - Chiến lược sản phẩm chi tiết
   - Chiến lược giá và định vị
   - Chiến lược phân phối (kênh nào mạnh)
   - Chiến lược số hóa
   - Điểm mạnh/yếu so sánh với đối thủ

3. SO SÁNH SẢN PHẨM THEO HẠNG MỤC:
   - Tiết kiệm: Ai dẫn đầu, gap analysis
   - Cho vay: Ai dẫn đầu, gap analysis  
   - Thẻ: Ai dẫn đầu, gap analysis
   - Digital: Ai dẫn đầu, gap analysis

4. CHIẾN LƯỢC KINH DOANH ĐỀ XUẤT:
   - Chiến lược tổng thể (Differentiation/Cost Leadership/Focus/Niche)
   - Chiến lược sản phẩm cụ thể (cần bổ sung/sửa gì)
   - Chiến lược giá (định vị giá đề xuất)
   - Chiến lược kênh phân phối (mở rộng kênh nào)
   - Chiến lược marketing (tiếp cận phân khúc nào)
   - Lộ trình thực thi 6-12-18 tháng với KPI cụ thể

5. CƠ HỘI THỊ TRƯỜNG:
   - Phân khúc chưa khai thác
   - Sản phẩm còn thiếu
   - Xu hướng cần bắt kịp (AI, embedded finance, v.v.)

OUTPUT JSON:
{{
    "executive_summary": "Tóm tắt chiến lược 3-4 câu cho CEO - bao quát toàn bộ phân tích",
    "competitive_ranking": [
        {{
            "rank": 1,
            "bank": "Tên ngân hàng",
            "position": "Leader/Challenger/Follower/Niche",
            "score": "X/10",
            "key_strength": "Điểm mạnh quyết định vị thế",
            "analysis": "Giải thích ngắn gọn tại sao xếp hạng này"
        }}
    ],
    "detailed_competitor_analysis": [
        {{
            "bank": "Tên ngân hàng",
            "market_position": "Mô tả vị thế chi tiết",
            "product_strategy": "Chiến lược sản phẩm",
            "pricing_strategy": "Chiến lược giá",
            "distribution_strategy": "Chiến lược phân phối",
            "digital_strategy": "Chiến lược số hóa",
            "competitive_score": {{
                "product_breadth": "1-10",
                "digital_capability": "1-10",
                "pricing_competitiveness": "1-10",
                "brand_strength": "1-10",
                "overall": "1-10"
            }},
            "key_threats": ["Mối đe dọa 1", "Mối đe dọa 2"],
            "key_opportunities": ["Cơ hội 1", "Cơ hội 2"]
        }}
    ],
    "product_comparison_matrix": {{
        "savings_products": {{"leader": "Ngân hàng", "gap_analysis": "Phân tích chi tiết"}},
        "loan_products": {{"leader": "Ngân hàng", "gap_analysis": "Phân tích chi tiết"}},
        "card_products": {{"leader": "Ngân hàng", "gap_analysis": "Phân tích chi tiết"}},
        "digital_products": {{"leader": "Ngân hàng", "gap_analysis": "Phân tích chi tiết"}}
    }},
    "strategic_recommendations": {{
        "overall_strategy": "Chiến lược tổng thể đề xuất chi tiết",
        "product_strategy": "Chiến lược sản phẩm cụ thể",
        "pricing_strategy": "Định vị giá đề xuất",
        "distribution_strategy": "Mở rộng kênh đề xuất",
        "digital_strategy": "Chuyển đổi số đề xuất",
        "implementation_roadmap": [
            {{
                "phase": "Giai đoạn 1 (0-6 tháng)",
                "actions": ["Hành động cụ thể 1", "Hành động 2"],
                "milestones": "KPI đạt được (VD: Tăng 20% sản phẩm mới)",
                "investment_required": "Mức đầu tư ước tính"
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
            "opportunity": "Cơ hội thị trường cụ thể",
            "rationale": "Lý do chi tiết",
            "potential_revenue": "Doanh thu tiềm năng ước tính",
            "difficulty": "Dễ/Trung bình/Khó",
            "priority": "Cao/Trung bình/Thấp"
        }}
    ],
    "risk_mitigation": ["Rủi ro và cách giảm thiểu"]
}}

JSON hợp lệ, không markdown."""

    try:
        content = call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=4000, retries=3)
        strategy = clean_json(content)
        
        if not strategy:
            # Retry với model khác
            content = call_groq_api(prompt, model="llama-3.1-70b-versatile", max_tokens=3500, retries=2)
            strategy = clean_json(content)
        
        if not strategy:
            raise Exception("Cannot parse strategy response")
            
        return strategy
        
    except Exception as e:
        # KHÔNG fallback - báo lỗi thật
        raise Exception(f"Strategy generation failed: {str(e)}")
