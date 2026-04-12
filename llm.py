from groq import Groq
import os
import json
import re

client = Groq(api_key=os.environ["GROQ_API_KEY_BK"])
MODEL = "llama-3.3-70b-versatile"  # Model mạnh nhất cho strategic analysis

def clean_json(text):
    """Làm sạch JSON từ LLM response"""
    try:
        return json.loads(text)
    except:
        # Try extract JSON block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

def analyze_strategy(results):
    """
    Deep Strategic Analysis - Phân tích chiến lược kinh doanh chuyên sâu
    """
    
    # Prepare rich context
    context = format_competitor_context(results)
    
    prompt = f"""
Bạn là CHUYÊN GIA TƯ VẤN CHIẾN LƯỢC NGÂN HÀNG HÀNG ĐẦU (McKinsey/Boston Consulting Group level).

NHIỆM VỤ: Phân tích cạnh tranh ngân hàng sâu và đề xuất chiến lược kinh doanh thực thi được.

DỮ LIỆU ĐỐI THỦ:
{context}

YÊU CẦU PHÂN TÍCH CHUYÊN SÂU:

1. PHÂN TÍCH CẠNH TRANH (Competitive Analysis):
   - Điểm mạnh/yếu từng đối thủ
   - Vị thế cạnh tranh (Leader/Challenger/Follower/Niche)
   - Ma trận cạnh tranh theo phân khúc

2. PHÂN TÍCH SẢN PHẨM (Product Portfolio Analysis):
   - Product mix của từng ngân hàng
   - Gaps và opportunities trong thị trường
   - Best practices cần học hỏi

3. CHIẾN LƯỢC KINH DOANH (Business Strategy):
   - Đề xuất 3-5 chiến lược cụ thể, khả thi
   - Kế hoạch hành động ưu tiên (Priority Action Plan)
   - KPIs để đo lường thành công

4. XU HƯỚNG THỊ TRƯỜNG (Market Trends):
   - Digital banking trends
   - Customer behavior shifts
   - Regulatory impacts

5. LỜI KHUYÊN CHIẾN LƯỢC (Strategic Recommendations):
   - Short-term (0-6 tháng)
   - Medium-term (6-18 tháng)
   - Long-term (18-36 tháng)

OUTPUT FORMAT - JSON STRICT:
{{
    "executive_summary": "Tóm tắt chiến lược 2-3 câu cho CEO",
    "competitive_landscape": {{
        "market_leader": "Tên ngân hàng dẫn đầu và lý do",
        "challengers": ["Ngân hàng thách thức"],
        "differentiation_factors": ["Yếu tố khác biệt hóa"]
    }},
    "competitor_analysis": [
        {{
            "bank": "Tên ngân hàng",
            "position": "Leader/Challenger/Follower/Niche",
            "strengths": ["Điểm mạnh"],
            "weaknesses": ["Điểm yếu"],
            "key_products": ["Sản phẩm chủ lực"],
            "competitive_threat": "High/Medium/Low"
        }}
    ],
    "market_gaps": [
        "Cơ hội thị trường chưa được khai thác"
    ],
    "strategic_recommendations": {{
        "immediate_actions": [
            {{
                "action": "Hành động cụ thể",
                "rationale": "Lý do chiến lược",
                "expected_impact": "Tác động dự kiến",
                "timeline": "Thời gian thực hiện",
                "resources_needed": "Nguồn lực cần thiết"
            }}
        ],
        "product_strategy": [
            "Chiến lược sản phẩm chi tiết"
        ],
        "digital_strategy": [
            "Chiến lược chuyển đổi số"
        ],
        "customer_strategy": [
            "Chiến lược khách hàng"
        ]
    }},
    "risk_mitigation": [
        "Rủi ro và cách giảm thiểu"
    ],
    "success_metrics": [
        "KPIs đo lường thành công"
    ]
}}

CHỈ TRẢ VỀ JSON. KHÔNG MARKDOWN. KHÔNG GIẢI THÍCH NGOÀI JSON.
"""

    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là senior banking strategist. Trả về JSON analysis chuyên sâu, không markdown."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        content = res.choices[0].message.content.strip()
        strategy = clean_json(content)

        if not strategy:
            # Retry with simpler approach
            strategy = generate_fallback_strategy(results)

        return strategy

    except Exception as e:
        return generate_fallback_strategy(results, str(e))

def format_competitor_context(results):
    """Format dữ liệu đối thủ cho context"""
    context_parts = []
    
    for idx, r in enumerate(results, 1):
        a = r.get("analysis", {})
        
        products_summary = []
        for p in a.get("products", []):
            if isinstance(p, dict):
                products_summary.append(f"{p.get('category', 'Unknown')}: {p.get('name', 'Unknown')}")
            else:
                products_summary.append(str(p))
        
        promos = [p.get("name", str(p)) for p in a.get("promotions", []) if isinstance(p, dict)] or a.get("promotions", [])
        
        ctx = f"""
BANK #{idx}: {a.get('bank_name', 'Unknown')}
- Products ({len(products_summary)}): {', '.join(products_summary[:5])}
- Interest Rates: {json.dumps(a.get('interest_rates', {}), ensure_ascii=False)}
- Promotions: {', '.join(promos[:3])}
- Digital: {', '.join(a.get('digital_capabilities', [])[:3])}
- Positioning: {a.get('positioning', 'N/A')}
- Strengths: {', '.join(a.get('strengths', [])[:3])}
"""
        context_parts.append(ctx)
    
    return "\n".join(context_parts)

def generate_fallback_strategy(results, error_msg=None):
    """Tạo strategy mặc định khi AI thất bại"""
    banks = [r.get("analysis", {}).get("bank_name", "Unknown") for r in results]
    
    return {
        "executive_summary": f"Phân tích {len(banks)} ngân hàng: {', '.join(banks)}. Cần chiến lược differentiation rõ ràng.",
        "competitive_landscape": {
            "market_leader": "Cần phân tích thêm để xác định",
            "challengers": banks[1:] if len(banks) > 1 else [],
            "differentiation_factors": ["Digital experience", "Product innovation", "Customer service"]
        },
        "competitor_analysis": [
            {
                "bank": b,
                "position": "Unknown",
                "strengths": ["Cần phân tích sâu hơn"],
                "weaknesses": ["Cần phân tích sâu hơn"],
                "key_products": [],
                "competitive_threat": "Unknown"
            } for b in banks
        ],
        "market_gaps": [
            "Personalized banking experience",
            "AI-powered financial advisory",
            "Seamless omnichannel integration"
        ],
        "strategic_recommendations": {
            "immediate_actions": [
                {
                    "action": "Audit lại toàn bộ product portfolio",
                    "rationale": "Cần hiểu rõ vị thế hiện tại",
                    "expected_impact": "Clarity on competitive position",
                    "timeline": "1-2 tháng",
                    "resources_needed": "Strategy team + external consultant"
                }
            ],
            "product_strategy": ["Focus on digital-first products", "Develop personalized offerings"],
            "digital_strategy": ["Invest in AI/ML capabilities", "Mobile-first approach"],
            "customer_strategy": ["Segment-based value proposition", "Enhanced customer journey"]
        },
        "risk_mitigation": ["Regulatory compliance", "Cybersecurity investment", "Talent acquisition"],
        "success_metrics": ["Customer acquisition cost", "Lifetime value", "Digital adoption rate", "NPS score"],
        "_note": "Fallback strategy generated" + (f" due to error: {error_msg}" if error_msg else "")
    }
