import os
import json
import re
import requests
import time


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


def call_ai_api(prompt, max_tokens=2000, retries=3):
    """Gọi Anthropic Claude API"""
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": (
            "Bạn là chuyên gia phân tích ngân hàng Việt Nam với 15 năm kinh nghiệm. "
            "Luôn trả về JSON hợp lệ, không có text nào bên ngoài JSON. "
            "Tất cả keys dùng snake_case (ví dụ: bank_name, không phải Bank_Name)."
        ),
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(retries):
        try:
            res = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=90)

            if res.status_code == 529 or res.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"⏳ API overloaded, waiting {wait}s...")
                time.sleep(wait)
                continue

            res.raise_for_status()
            data = res.json()

            # Lấy text từ response
            content_blocks = data.get("content", [])
            text = " ".join(
                block.get("text", "") for block in content_blocks if block.get("type") == "text"
            ).strip()

            return text

        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout attempt {attempt + 1}")
            if attempt < retries - 1:
                time.sleep(5)
        except Exception as e:
            print(f"⚠️ API error attempt {attempt + 1}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                raise

    raise Exception("AI API failed after all retries")


# Alias cho backward compatibility
def call_groq_api(prompt, model=None, max_tokens=1500, retries=3):
    """Backward compat wrapper"""
    return call_ai_api(prompt, max_tokens=max_tokens, retries=retries)


def clean_json(text):
    """Parse JSON từ response AI, xử lý nhiều format khác nhau"""
    if not text:
        return None

    # Thử parse trực tiếp
    try:
        return json.loads(text)
    except:
        pass

    # Tìm JSON trong ```json ... ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # Tìm JSON trong ``` ... ```
    match = re.search(r'```\s*([\s\S]*?)\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # Tìm object JSON đầu tiên
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            # Thử fix JSON bị cắt bởi max_tokens
            raw = match.group()
            # Đếm braces để tìm điểm kết thúc
            depth = 0
            end = 0
            for i, ch in enumerate(raw):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end:
                try:
                    return json.loads(raw[:end])
                except:
                    pass

    return None


def analyze_strategy(results):
    """Tạo phân tích chiến lược tổng thể từ kết quả các ngân hàng"""
    if not results:
        return {
            "executive_summary": "Không có dữ liệu để phân tích.",
            "competitive_ranking": [],
            "strategic_recommendations": {"overall_strategy": "N/A"}
        }

    # Tóm tắt dữ liệu cho AI
    summary = []
    for r in results:
        a = r.get("analysis", {})
        strategic = a.get("strategic_analysis", {})
        competitive = a.get("competitive_assessment", {})
        summary.append({
            "bank": a.get("bank_name", "Unknown"),
            "code": a.get("bank_code", ""),
            "product_count": len(a.get("products", [])),
            "digital_count": len(a.get("digital_capabilities", [])),
            "positioning": strategic.get("positioning", "")[:100],
            "strengths": competitive.get("strengths", [])[:3],
            "weaknesses": competitive.get("weaknesses", [])[:2],
            "market_position": competitive.get("market_position", ""),
            "threat_level": competitive.get("competitive_threat_level", ""),
            "interest_rates": a.get("interest_rates", {})
        })

    prompt = f"""Phân tích cạnh tranh và chiến lược cho các ngân hàng Việt Nam sau:

{json.dumps(summary, ensure_ascii=False, indent=2)}

Trả về DUY NHẤT một JSON object (không có text nào khác) với cấu trúc:
{{
  "executive_summary": "Tóm tắt toàn cảnh thị trường ngân hàng Việt Nam và vị thế các ngân hàng...",
  "competitive_ranking": [
    {{
      "rank": 1,
      "bank": "Tên ngân hàng",
      "position": "Vị thế thị trường",
      "score": "8.5",
      "key_strength": "Điểm mạnh cốt lõi",
      "analysis": "Phân tích ngắn 1-2 câu"
    }}
  ],
  "detailed_competitor_analysis": [
    {{
      "bank": "Tên ngân hàng",
      "product_strategy": "Chiến lược sản phẩm chi tiết",
      "pricing_strategy": "Chiến lược giá và định vị",
      "distribution_strategy": "Chiến lược phân phối kênh",
      "digital_strategy": "Chiến lược số hóa",
      "competitive_score": {{
        "product_breadth": 8,
        "digital_capability": 7,
        "pricing_competitiveness": 8,
        "brand_strength": 9,
        "overall": 8
      }},
      "key_threats": ["Mối đe dọa 1", "mối đe dọa 2"],
      "key_opportunities": ["Cơ hội 1", "cơ hội 2"]
    }}
  ],
  "product_comparison_matrix": {{
    "Tiết kiệm": {{"leader": "Tên ngân hàng dẫn đầu", "gap_analysis": "Phân tích khoảng cách"}},
    "Cho vay": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}},
    "Thẻ": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}},
    "Ngân hàng số": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}}
  }},
  "strategic_recommendations": {{
    "overall_strategy": "Chiến lược tổng thể để cạnh tranh hiệu quả",
    "product_strategy": "Gợi ý phát triển sản phẩm",
    "pricing_strategy": "Chiến lược giá đề xuất",
    "distribution_strategy": "Chiến lược kênh phân phối",
    "digital_strategy": "Ưu tiên số hóa",
    "implementation_roadmap": [
      {{
        "phase": "Giai đoạn 1 (Q1-Q2 2025)",
        "actions": ["Hành động 1", "Hành động 2", "Hành động 3"],
        "milestones": "KPI đo lường",
        "investment_required": "Mức đầu tư ước tính"
      }},
      {{
        "phase": "Giai đoạn 2 (Q3-Q4 2025)",
        "actions": ["Hành động 1", "Hành động 2"],
        "milestones": "KPI",
        "investment_required": "Mức đầu tư"
      }}
    ]
  }},
  "market_opportunities": [
    {{
      "opportunity": "Tên cơ hội thị trường",
      "rationale": "Lý do và bằng chứng",
      "potential_revenue": "Tiềm năng doanh thu",
      "difficulty": "Dễ/Trung bình/Khó",
      "priority": "Cao/Trung bình/Thấp"
    }}
  ],
  "risk_mitigation": [
    "Rủi ro 1 và cách giảm thiểu",
    "Rủi ro 2 và cách giảm thiểu",
    "Rủi ro 3 và cách giảm thiểu"
  ]
}}"""

    try:
        content = call_ai_api(prompt, max_tokens=3000, retries=2)
        strategy = clean_json(content)

        if not strategy:
            raise Exception("Cannot parse strategy JSON")

        # Đảm bảo keys snake_case nhất quán
        return normalize_keys(strategy)

    except Exception as e:
        print(f"❌ Strategy analysis failed: {str(e)}")
        return {
            "executive_summary": f"Lỗi khi phân tích chiến lược: {str(e)}. Vui lòng xem chi tiết từng ngân hàng bên trái.",
            "competitive_ranking": [
                {"rank": i+1, "bank": r.get("bank", ""), "position": r.get("market_position", "N/A"),
                 "score": "N/A", "key_strength": "", "analysis": ""}
                for i, r in enumerate(summary)
            ],
            "strategic_recommendations": {
                "overall_strategy": "Vui lòng thử lại để nhận phân tích chiến lược đầy đủ.",
            }
        }


def normalize_keys(obj):
    """Đảm bảo tất cả keys dùng snake_case nhất quán"""
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            # Chuyển CamelCase và Camel_Case về snake_case
            new_key = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', k).lower()
            new_key = new_key.replace(' ', '_')
            new_obj[new_key] = normalize_keys(v)
        return new_obj
    elif isinstance(obj, list):
        return [normalize_keys(item) for item in obj]
    return obj
