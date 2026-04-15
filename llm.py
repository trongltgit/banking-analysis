import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def call_groq_api(prompt, model="llama-3.3-70b-versatile", max_tokens=1500, retries=3):
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia phân tích ngân hàng. Trả về JSON với key CHỮ HOA đầu từ (ví dụ: Executive_summary, Competitive_ranking)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }

    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=70)
            
            if res.status_code == 429:
                wait = 7 * (attempt + 1)
                print(f"⏳ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
                
            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]
            
            # Xử lý trường hợp AI trả về JSON nằm trong block ```json ... ```
            if "```json" in content:
                content = re.search(r"```json\n([\s\S]*?)\n```", content).group(1)
            elif "```" in content:
                content = re.search(r"```([\s\S]*?)```", content).group(1)
                
            return content.strip()

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
                continue
            raise
    raise Exception("Groq API failed after retries")

def to_camel_case(obj):
    """Chuyển đổi tất cả key trong dict từ snake_case sang Camel_Case"""
    if isinstance(obj, dict):
        return {convert_key(k): to_camel_case(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_camel_case(item) for item in obj]
    else:
        return obj

def convert_key(key):
    """Chuyển snake_case sang Camel_Case"""
    # Các key đặc biệt cần giữ nguyên hoặc xử lý riêng
    special_keys = {
        'url': 'url',
        'extraction_quality': 'extraction_quality'
    }
    if key in special_keys:
        return special_keys[key]
    
    # Chuyển đổi snake_case sang Camel_Case
    parts = key.split('_')
    return '_'.join([p.capitalize() for p in parts])

def analyze_strategy(results):
    if not results:
        return {
            "Executive_summary": "Không có dữ liệu đầu vào để phân tích chiến lược.",
            "Competitive_ranking": [],
            "Strategic_recommendations": {"Overall_strategy": "N/A", "Immediate_actions": []}
        }

    # Rút gọn dữ liệu để gửi cho AI
    summary = []
    for r in results:
        a = r.get("analysis", {})
        summary.append({
            "bank": a.get("bank_name", "Unknown"),
            "products": len(a.get("products", [])),
            "position": a.get("strategic_analysis", {}).get("positioning", "")[:60],
            "strengths": a.get("competitive_assessment", {}).get("strengths", [])[:2]
        })

    prompt = f"""Phân tích các ngân hàng sau và đưa ra chiến lược cạnh tranh:

{json.dumps(summary, ensure_ascii=False, indent=2)}

Trả về DUY NHẤT một JSON object với key CHỮ HOA theo cấu trúc:
{{
  "Executive_summary": "Tóm tắt chiến lược tổng quan...",
  "Competitive_ranking": [
    {{"Rank": 1, "Bank": "Tên ngân hàng", "Position": "Vị thế", "Score": "8.5", "Key_strength": "Điểm mạnh chính", "Analysis": "Phân tích ngắn"}}
  ],
  "Detailed_competitor_analysis": [
    {{"Bank": "Tên", "Product_strategy": "...", "Pricing_strategy": "...", "Distribution_strategy": "...", "Digital_strategy": "...", 
      "Competitive_score": {{"Product_breadth": 8, "Digital_capability": 7, "Pricing_competitiveness": 8, "Brand_strength": 9, "Overall": 8}},
      "Key_threats": ["..."], "Key_opportunities": ["..."]}}
  ],
  "Product_comparison_matrix": {{"Savings": {{"Leader": "Bank A", "Gap_analysis": "..."}},
  "Strategic_recommendations": {{
    "Overall_strategy": "...",
    "Product_strategy": "...",
    "Pricing_strategy": "...",
    "Distribution_strategy": "...",
    "Digital_strategy": "...",
    "Implementation_roadmap": [
      {{"Phase": "Giai đoạn 1", "Actions": ["Hành động 1", "Hành động 2"], "Milestones": "KPI", "Investment_required": "Chi phí"}}
    ]
  }},
  "Market_opportunities": [
    {{"Opportunity": "Cơ hội", "Rationale": "Lý do", "Potential_revenue": "Doanh thu", "Difficulty": "Trung bình", "Priority": "Cao"}}
  ],
  "Risk_mitigation": ["Rủi ro 1", "Rủi ro 2"]
}}

Lưu ý: Tất cả key phải CHỮ HOA đầu từ (Executive_summary, không phải executive_summary)."""

    try:
        content = call_groq_api(prompt, max_tokens=2000, retries=2)
        
        # Parse JSON từ AI
        try:
            strategy = json.loads(content)
        except json.JSONDecodeError:
            # Thử tìm JSON trong text
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                strategy = json.loads(match.group())
            else:
                raise
        
        # Chuyển đổi key sang chữ hoa nếu AI trả về chữ thường
        strategy = to_camel_case(strategy)
        
        return strategy
        
    except Exception as e:
        print(f"❌ Strategy parse error: {str(e)}")
        # Fallback
        return {
            "Executive_summary": "Có lỗi khi tổng hợp chiến lược bằng AI.",
            "Competitive_ranking": [{"Rank": 1, "Bank": r.get("bank", "Bank"), "Position": "N/A", "Score": "N/A"} for r in summary],
            "Strategic_recommendations": {
                "Overall_strategy": "Vui lòng kiểm tra dữ liệu chi tiết của từng ngân hàng.",
                "Product_strategy": "Cần xem xét thủ công.",
                "Immediate_actions": ["Tải lại trang hoặc thử lại sau"]
            }
        }
