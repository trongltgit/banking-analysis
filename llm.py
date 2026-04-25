import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Luân phiên model khi bị rate limit
GROQ_MODELS = [
    "llama-3.3-70b-versatile",   # Mạnh nhất, dùng trước
    "llama-3.1-8b-instant",      # Nhanh, ít bị limit
    "gemma2-9b-it",              # Backup 1
    "mixtral-8x7b-32768",        # Backup 2
]


def call_ai_api(prompt, max_tokens=2000, retries=4):
    """Gọi Groq API với smart retry + model rotation"""
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK chưa được set trong environment variables")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    last_error = None

    for attempt in range(retries):
        model = GROQ_MODELS[attempt % len(GROQ_MODELS)]

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Bạn là chuyên gia phân tích ngân hàng Việt Nam. "
                        "Luôn trả về JSON hợp lệ, không có text nào bên ngoài JSON. "
                        "Tất cả keys dùng snake_case (bank_name, executive_summary...)."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens
        }

        try:
            print(f"🤖 Groq [{model}] attempt {attempt + 1}/{retries}...")
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)

            if res.status_code == 429:
                # Đọc Retry-After header nếu có
                retry_after = int(res.headers.get("Retry-After", 0))
                wait = max(retry_after, 8 * (attempt + 1))
                print(f"⏳ Rate limited [{model}], waiting {wait}s then trying next model...")
                time.sleep(wait)
                last_error = f"Rate limit on {model}"
                continue

            if res.status_code == 404:
                print(f"⚠️ Model {model} not available, switching...")
                last_error = f"Model {model} not found"
                continue

            res.raise_for_status()

            content = res.json()["choices"][0]["message"]["content"].strip()

            # Strip markdown code fences nếu có
            content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)

            print(f"✅ Groq OK [{model}] ({len(content)} chars)")
            return content.strip()

        except requests.exceptions.Timeout:
            wait = 5 * (attempt + 1)
            print(f"⏱️ Timeout [{model}], waiting {wait}s...")
            time.sleep(wait)
            last_error = f"Timeout on {model}"

        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"❌ Error [{model}]: {str(e)}, waiting {wait}s...")
            time.sleep(wait)
            last_error = str(e)

    raise Exception(f"Groq API failed after {retries} attempts. Last error: {last_error}")


# Backward compat
def call_groq_api(prompt, model=None, max_tokens=1500, retries=3):
    return call_ai_api(prompt, max_tokens=max_tokens, retries=retries)


def clean_json(text):
    """Parse JSON từ response AI, xử lý nhiều format"""
    if not text:
        return None

    # Thử parse trực tiếp
    try:
        return json.loads(text)
    except:
        pass

    # JSON trong ```json ... ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # JSON trong ``` ... ```
    match = re.search(r'```\s*([\s\S]*?)\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # Tìm object JSON đầu tiên trong text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        raw = match.group()
        try:
            return json.loads(raw)
        except:
            # Thử fix JSON bị cắt bởi max_tokens
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


def normalize_keys(obj):
    """Chuyển tất cả keys về snake_case nhất quán"""
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            new_key = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', k).lower()
            new_key = new_key.replace(' ', '_').replace('-', '_')
            new_obj[new_key] = normalize_keys(v)
        return new_obj
    elif isinstance(obj, list):
        return [normalize_keys(item) for item in obj]
    return obj


def analyze_strategy(results):
    """Phân tích chiến lược tổng thể từ kết quả các ngân hàng"""
    if not results:
        return {
            "executive_summary": "Không có dữ liệu để phân tích.",
            "competitive_ranking": [],
            "strategic_recommendations": {"overall_strategy": "N/A"}
        }

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
            "interest_rates": a.get("interest_rates", {})
        })

    prompt = f"""Phân tích cạnh tranh và chiến lược cho các ngân hàng Việt Nam sau:

{json.dumps(summary, ensure_ascii=False, indent=2)}

Trả về DUY NHẤT một JSON object (không có text nào khác) với cấu trúc:
{{
  "executive_summary": "Tóm tắt toàn cảnh thị trường và vị thế các ngân hàng...",
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
      "product_strategy": "Chiến lược sản phẩm",
      "pricing_strategy": "Chiến lược giá",
      "distribution_strategy": "Chiến lược phân phối",
      "digital_strategy": "Chiến lược số hóa",
      "competitive_score": {{
        "product_breadth": 8,
        "digital_capability": 7,
        "pricing_competitiveness": 8,
        "brand_strength": 9,
        "overall": 8
      }},
      "key_threats": ["Mối đe dọa 1"],
      "key_opportunities": ["Cơ hội 1"]
    }}
  ],
  "product_comparison_matrix": {{
    "Tiết kiệm": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}},
    "Cho vay": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}},
    "Thẻ": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}},
    "Ngân hàng số": {{"leader": "Tên ngân hàng", "gap_analysis": "Phân tích"}}
  }},
  "strategic_recommendations": {{
    "overall_strategy": "Chiến lược tổng thể",
    "product_strategy": "Chiến lược sản phẩm",
    "pricing_strategy": "Chiến lược giá",
    "distribution_strategy": "Chiến lược phân phối",
    "digital_strategy": "Chiến lược số hóa",
    "implementation_roadmap": [
      {{
        "phase": "Giai đoạn 1 (Q1-Q2 2025)",
        "actions": ["Hành động 1", "Hành động 2"],
        "milestones": "KPI đo lường",
        "investment_required": "Ước tính đầu tư"
      }}
    ]
  }},
  "market_opportunities": [
    {{
      "opportunity": "Tên cơ hội",
      "rationale": "Lý do",
      "potential_revenue": "Tiềm năng",
      "difficulty": "Dễ/Trung bình/Khó",
      "priority": "Cao/Trung bình/Thấp"
    }}
  ],
  "risk_mitigation": ["Rủi ro 1 và cách giảm thiểu", "Rủi ro 2"]
}}"""

    try:
        content = call_ai_api(prompt, max_tokens=2500, retries=3)
        strategy = clean_json(content)

        if not strategy:
            raise Exception("Cannot parse strategy JSON")

        return normalize_keys(strategy)

    except Exception as e:
        print(f"❌ Strategy analysis failed: {str(e)}")
        return {
            "executive_summary": f"Lỗi khi phân tích chiến lược: {str(e)}. Xem chi tiết từng ngân hàng bên trái.",
            "competitive_ranking": [
                {
                    "rank": i + 1,
                    "bank": r.get("bank", ""),
                    "position": r.get("market_position", "N/A"),
                    "score": "N/A",
                    "key_strength": "",
                    "analysis": ""
                }
                for i, r in enumerate(summary)
            ],
            "strategic_recommendations": {
                "overall_strategy": "Vui lòng thử lại để nhận phân tích đầy đủ."
            }
        }
