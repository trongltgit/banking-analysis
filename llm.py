import os
import json
import re
import requests
import time

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Model rotation - mạnh nhất trước
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]


def call_ai_api(prompt, max_tokens=3000, retries=5):
    """Gọi GROQ API với smart retry + model rotation"""
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
                        "Bạn là chuyên gia phân tích kinh doanh và chiến lược cấp cao. "
                        "Luôn trả về JSON hợp lệ, không có bất kỳ text nào bên ngoài JSON. "
                        "Không dùng markdown code blocks. Chỉ trả về object JSON thuần túy. "
                        "Tất cả keys dùng snake_case. Phân tích dựa trên dữ liệu thực tế được cung cấp."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.15,
            "max_tokens": max_tokens,
            "top_p": 0.9
        }

        try:
            print(f"🤖 GROQ [{model}] attempt {attempt+1}/{retries}...")
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)

            if res.status_code == 429:
                retry_after = int(res.headers.get("Retry-After", 0))
                wait = max(retry_after, 10 * (attempt + 1))
                print(f"⏳ Rate limited [{model}], waiting {wait}s, switching model...")
                time.sleep(wait)
                last_error = f"Rate limit on {model}"
                continue

            if res.status_code in [404, 400]:
                resp_json = res.json() if res.content else {}
                err_msg = resp_json.get("error", {}).get("message", "")
                print(f"⚠️ Model {model} error {res.status_code}: {err_msg}, switching...")
                last_error = f"Model {model} error: {err_msg}"
                time.sleep(2)
                continue

            if res.status_code == 503:
                wait = 15 * (attempt + 1)
                print(f"⏳ Service unavailable, waiting {wait}s...")
                time.sleep(wait)
                last_error = "Service unavailable"
                continue

            res.raise_for_status()

            content = res.json()["choices"][0]["message"]["content"].strip()

            # Strip markdown code fences
            content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            content = content.strip()

            print(f"✅ GROQ OK [{model}] ({len(content)} chars)")
            return content

        except requests.exceptions.Timeout:
            wait = 8 * (attempt + 1)
            print(f"⏱️ Timeout [{model}], waiting {wait}s...")
            time.sleep(wait)
            last_error = f"Timeout on {model}"

        except requests.exceptions.ConnectionError as e:
            wait = 10
            print(f"🔌 Connection error [{model}]: {str(e)[:60]}, waiting {wait}s...")
            time.sleep(wait)
            last_error = str(e)

        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"❌ Error [{model}]: {str(e)[:80]}, waiting {wait}s...")
            time.sleep(wait)
            last_error = str(e)

    raise Exception(f"GROQ API failed after {retries} attempts. Last error: {last_error}")


# Backward compat
def call_groq_api(prompt, model=None, max_tokens=1500, retries=3):
    return call_ai_api(prompt, max_tokens=max_tokens, retries=retries)


def clean_json(text):
    """Parse JSON từ AI response, xử lý nhiều format"""
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

    # Tìm JSON object đầu tiên trong text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        raw = match.group()
        try:
            return json.loads(raw)
        except:
            # Thử fix JSON bị cắt
            depth = 0
            end = 0
            in_string = False
            escape_next = False
            for i, ch in enumerate(raw):
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\' and in_string:
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                if not in_string:
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

    # Thử extract JSON array
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return None


def normalize_keys(obj):
    """Chuyển tất cả keys về snake_case"""
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
    """Phân tích chiến lược cạnh tranh tổng thể từ dữ liệu thực tế các tổ chức"""
    if not results:
        return {
            "executive_summary": "Không có dữ liệu để phân tích.",
            "competitive_ranking": [],
            "strategic_recommendations": {"overall_strategy": "N/A"}
        }

    # Tóm tắt dữ liệu từng entity
    summary = []
    for r in results:
        a = r.get("analysis", {})
        strategic = a.get("strategic_analysis", {})
        competitive = a.get("competitive_assessment", {})
        pricing = a.get("pricing", {})

        # Lấy tên products cụ thể
        products = a.get("products", [])
        product_names = []
        product_by_category = {}
        for p in products:
            if isinstance(p, dict):
                cat = p.get("category", "OTHER")
                name = p.get("name", "")
                product_by_category.setdefault(cat, []).append(name)
                product_names.append(f"{cat}:{name}")
            elif isinstance(p, str):
                product_names.append(p)

        summary.append({
            "entity": a.get("entity_name", a.get("bank_name", "Unknown")),
            "code": a.get("entity_code", a.get("bank_code", "")),
            "type": r.get("entity_type", a.get("entity_type", "company")),
            "product_count": len(products),
            "product_categories": list(product_by_category.keys()),
            "sample_products": product_names[:15],
            "digital_count": len(a.get("digital_capabilities", [])),
            "digital_features": a.get("digital_capabilities", [])[:8],
            "positioning": strategic.get("positioning", "")[:120],
            "value_proposition": strategic.get("value_proposition", "")[:100],
            "target_segments": strategic.get("target_segments", [])[:4],
            "key_differentiators": strategic.get("key_differentiators", [])[:4],
            "strengths": competitive.get("strengths", [])[:4],
            "weaknesses": competitive.get("weaknesses", [])[:3],
            "unique_selling_points": competitive.get("unique_selling_points", [])[:3],
            "market_position": competitive.get("market_position", ""),
            "threat_level": competitive.get("competitive_threat_level", ""),
            "interest_rates": a.get("interest_rates", pricing.get("interest_rates", {})),
            "promotions_count": len(a.get("promotions", pricing.get("promotions", []))),
            "data_confidence": a.get("data_confidence", "medium"),
            "extraction_quality": r.get("extraction_quality", "limited"),
            "source": r.get("source", "unknown")
        })

    entity_type_label = "ngân hàng/tổ chức tài chính" if any(
        s.get("type") == "bank" for s in summary
    ) else "công ty/tổ chức"

    prompt = f"""Bạn là chuyên gia tư vấn chiến lược cấp cao (McKinsey level). Phân tích cạnh tranh chuyên sâu dựa trên dữ liệu THỰC TẾ đã thu thập từ các {entity_type_label} sau:

{json.dumps(summary, ensure_ascii=False, indent=2)}

Phân tích THỰC TẾ, sâu sắc, có insight cụ thể. KHÔNG chung chung, KHÔNG bịa số liệu.

Trả về DUY NHẤT JSON object (không có text nào khác):
{{
  "executive_summary": "Tóm tắt toàn cảnh thị trường: ai đang dẫn đầu, ai đang thách thức, xu hướng chính, cơ hội và rủi ro trọng yếu. Tối thiểu 3-4 câu với insight thực tế.",

  "market_overview": {{
    "total_entities_analyzed": {len(summary)},
    "market_dynamics": "Động lực cạnh tranh chính của thị trường này",
    "key_trends": ["Xu hướng 1 nhận thấy từ dữ liệu", "Xu hướng 2", "Xu hướng 3"],
    "disruption_factors": ["Yếu tố disruption 1", "Yếu tố 2"]
  }},

  "competitive_ranking": [
    {{
      "rank": 1,
      "entity": "Tên tổ chức",
      "position": "Vị thế thị trường cụ thể",
      "score": "8.5",
      "key_strength": "Điểm mạnh cốt lõi nổi bật nhất",
      "key_weakness": "Điểm yếu lớn nhất",
      "analysis": "Phân tích 2-3 câu về vị thế cạnh tranh thực tế"
    }}
  ],

  "detailed_competitor_analysis": [
    {{
      "entity": "Tên tổ chức",
      "entity_type": "bank/company/fintech/insurance",
      "product_strategy": "Chiến lược danh mục sản phẩm - rộng hay tập trung, premium hay mass market",
      "pricing_strategy": "Chiến lược giá cụ thể - cạnh tranh về giá, value-based hay premium",
      "distribution_strategy": "Kênh phân phối chính - digital-first, branch network, partnership",
      "digital_strategy": "Mức độ số hóa và chiến lược digital cụ thể",
      "target_customer": "Phân khúc khách hàng chính",
      "competitive_score": {{
        "product_breadth": 7,
        "digital_capability": 8,
        "pricing_competitiveness": 7,
        "brand_strength": 8,
        "customer_experience": 7,
        "innovation": 6,
        "overall": 7
      }},
      "key_threats": ["Mối đe dọa cụ thể 1", "Mối đe dọa 2"],
      "key_opportunities": ["Cơ hội cụ thể 1", "Cơ hội 2"],
      "strategic_verdict": "Nhận định chiến lược tổng thể 1-2 câu"
    }}
  ],

  "product_comparison_matrix": {{
    "Sản phẩm chính": {{
      "leader": "Tên tổ chức dẫn đầu",
      "ranking": ["1st: Tên", "2nd: Tên", "3rd: Tên"],
      "gap_analysis": "Khoảng cách và đặc điểm khác biệt"
    }},
    "Năng lực Digital": {{
      "leader": "Tên tổ chức",
      "ranking": ["1st: Tên", "2nd: Tên"],
      "gap_analysis": "Phân tích khoảng cách digital"
    }},
    "Giá cả/Phí": {{
      "leader": "Tổ chức có giá cạnh tranh nhất",
      "ranking": ["1st: Tên", "2nd: Tên"],
      "gap_analysis": "Phân tích về mức giá và phí"
    }},
    "Trải nghiệm KH": {{
      "leader": "Tên tổ chức",
      "ranking": ["1st: Tên", "2nd: Tên"],
      "gap_analysis": "UX/CX khác biệt thế nào"
    }}
  }},

  "strategic_recommendations": {{
    "overall_strategy": "Chiến lược tổng thể cho tổ chức muốn cạnh tranh hiệu quả nhất trong thị trường này",
    "product_strategy": "Nên tập trung vào sản phẩm nào, bỏ gì, thêm gì",
    "pricing_strategy": "Định vị giá thế nào để tạo lợi thế",
    "distribution_strategy": "Kênh phân phối ưu tiên",
    "digital_strategy": "Roadmap số hóa cụ thể",
    "quick_wins": ["Việc có thể làm ngay (0-3 tháng) 1", "Quick win 2", "Quick win 3"],
    "implementation_roadmap": [
      {{
        "phase": "Giai đoạn 1 (Q1-Q2)",
        "objective": "Mục tiêu chính",
        "actions": ["Hành động cụ thể 1", "Hành động 2", "Hành động 3"],
        "milestones": "KPI đo lường cụ thể",
        "investment_required": "Ước tính nguồn lực"
      }},
      {{
        "phase": "Giai đoạn 2 (Q3-Q4)",
        "objective": "Mục tiêu chính",
        "actions": ["Hành động 1", "Hành động 2"],
        "milestones": "KPI",
        "investment_required": "Nguồn lực"
      }},
      {{
        "phase": "Giai đoạn 3 (Năm 2)",
        "objective": "Mục tiêu dài hạn",
        "actions": ["Hành động 1", "Hành động 2"],
        "milestones": "KPI dài hạn",
        "investment_required": "Đầu tư lớn"
      }}
    ]
  }},

  "market_opportunities": [
    {{
      "opportunity": "Tên cơ hội cụ thể",
      "rationale": "Lý do tại sao đây là cơ hội - dựa trên gap phân tích",
      "potential_impact": "Tác động tiềm năng",
      "difficulty": "Dễ/Trung bình/Khó",
      "priority": "Cao/Trung bình/Thấp",
      "who_should_pursue": "Tổ chức nào phù hợp nhất để khai thác"
    }}
  ],

  "risk_mitigation": [
    {{
      "risk": "Rủi ro cụ thể",
      "impact": "High/Medium/Low",
      "mitigation": "Cách giảm thiểu cụ thể"
    }}
  ],

  "competitive_intelligence_summary": {{
    "biggest_winner": "Tổ chức đang thắng nhất và lý do",
    "biggest_threat": "Tổ chức đe dọa nhất và tại sao",
    "hidden_gem": "Tổ chức được đánh giá thấp nhưng có tiềm năng",
    "key_battleground": "Mặt trận cạnh tranh chính hiện tại"
  }}
}}"""

    try:
        content = call_ai_api(prompt, max_tokens=3500, retries=4)
        strategy = clean_json(content)

        if not strategy:
            raise Exception("Cannot parse strategy JSON")

        return normalize_keys(strategy)

    except Exception as e:
        print(f"❌ Strategy analysis failed: {str(e)}")
        return {
            "executive_summary": f"Lỗi khi tổng hợp chiến lược: {str(e)}. Xem chi tiết từng tổ chức bên trái.",
            "market_overview": {"total_entities_analyzed": len(summary)},
            "competitive_ranking": [
                {
                    "rank": i + 1,
                    "entity": s.get("entity", ""),
                    "position": s.get("market_position", "N/A"),
                    "score": "N/A",
                    "key_strength": ", ".join(s.get("strengths", [])[:1]),
                    "analysis": s.get("positioning", "")
                }
                for i, s in enumerate(summary)
            ],
            "strategic_recommendations": {
                "overall_strategy": "Không thể tổng hợp chiến lược. Vui lòng thử lại."
            }
        }
