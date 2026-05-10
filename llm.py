"""
╔══════════════════════════════════════════════════════════════╗
║  DEEP BANKING INTELLIGENCE ENGINE — LLM CORE v3.0           ║
║  Multi-Model AI Pipeline | CAMELS Framework | Basel III      ║
║  Free Tier: Groq API (llama-3.3-70b, llama-3.1-70b, etc.)   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import json
import re
import requests
import time
from typing import Optional

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ─── MODEL TIERS (tất cả FREE trên Groq) ───────────────────────────────────
# Tier 1 — Ultra Deep Analysis (70B params, best reasoning)
# ⚠️ Đã xóa model bị khai tử: llama-3.1-70b-versatile, mixtral-8x7b-32768
TIER1_MODELS = [
    "llama-3.3-70b-versatile",
]
# ─── FIX 1: Đã xóa "gemma2-9b-it" (bị Groq khai tử) ───────────────────────
TIER2_MODELS = [
    "llama-3.1-8b-instant",
    "llama3-8b-8192",       # Thay thế cho gemma2-9b-it
]
ALL_MODELS = TIER1_MODELS + TIER2_MODELS

# Cap sleep để không vượt gunicorn timeout (300s)
MAX_RATE_LIMIT_SLEEP = 55

# ─── EXPERT PERSONAS ────────────────────────────────────────────────────────
EXPERT_BANKING_SYSTEM = """You are a Senior Banking Intelligence Analyst with 20+ years experience at Goldman Sachs, McKinsey Financial Services, IMF FSAP, and Basel Committee on Banking Supervision.

Your analytical framework: CAMELS Rating System, Porter Five Forces, BCG Growth-Share Matrix, SWOT + TOWS Strategic Matrix, Digital Maturity Model (DMM).

You ALWAYS:
- Provide quantitative scoring (1-10) with clear rationale
- Reference specific products/features found in data
- Identify strategic gaps and white spaces
- Compare against global best practices (JPMorgan, DBS, Nubank benchmarks)
- Output ONLY valid JSON, no markdown, no text outside JSON
- Never fabricate data not present in source material
- Write ALL text values in VIETNAMESE (Tiếng Việt). JSON keys stay in snake_case English."""

EXPERT_STRATEGY_SYSTEM = """You are the Head of Strategy at a top-tier global consultancy (McKinsey x Bain x BCG trained).
Specialty: Financial Services Competitive Intelligence for Asia-Pacific banking sector.

Standards: every claim evidence-based, MECE principle, 3x3 risk matrix.
Benchmarks: Techcombank (tech leader), VCB (brand leader), VPBank (growth leader).
Write ALL text values in VIETNAMESE (Tiếng Việt). JSON keys in snake_case English.
Output ONLY valid JSON. No preamble. No markdown."""

EXPERT_EXTRACTION_SYSTEM = """You are a Precision Data Extraction Engine for financial services.
Rules: extract ONLY data present in source, no hallucination, map to standard banking categories, flag data confidence.
Write ALL text values in VIETNAMESE (Tiếng Việt). JSON keys in English.
Output ONLY valid JSON. Zero tolerance for markdown."""


def call_ai_api(prompt, max_tokens=3000, retries=5, system_prompt=None,
                tier="auto", temperature=0.1):
    """Multi-tier AI caller with smart retry, model rotation, expert persona injection."""
    if system_prompt is None:
        system_prompt = EXPERT_BANKING_SYSTEM

    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set in environment variables")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if tier == "ultra":
        model_pool = TIER1_MODELS * 2 + TIER2_MODELS
    elif tier == "fast":
        model_pool = TIER2_MODELS * 2 + TIER1_MODELS
    else:
        model_pool = ALL_MODELS

    last_error = None
    for attempt in range(retries):
        model = model_pool[attempt % len(model_pool)]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
        }
        try:
            print(f"  🧠 [{model}] attempt {attempt+1}/{retries}")
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)

            if res.status_code == 429:
                raw_wait = int(res.headers.get("Retry-After", 0))
                wait = min(max(raw_wait, 12 * (attempt + 1)), MAX_RATE_LIMIT_SLEEP)
                print(f"  ⏳ Rate limit (server yêu cầu {raw_wait}s) → chờ {wait}s rồi đổi model...")
                time.sleep(wait)
                last_error = f"Rate limit on {model}"
                continue
            if res.status_code in [404, 400]:
                resp_j = res.json() if res.content else {}
                err = resp_j.get("error", {}).get("message", "")
                print(f"  ⚠️ [{model}] {res.status_code}: {err[:60]}")
                last_error = err
                time.sleep(2)
                continue
            if res.status_code == 503:
                wait = 15 * (attempt + 1)
                time.sleep(wait)
                last_error = "Service unavailable"
                continue

            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"].strip()
            content = re.sub(r'^```json\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            content = content.strip()
            print(f"  ✅ [{model}] → {len(content)} chars")
            return content

        except requests.exceptions.Timeout:
            time.sleep(min(8 * (attempt + 1), MAX_RATE_LIMIT_SLEEP))
            last_error = f"Timeout on {model}"
        except requests.exceptions.ConnectionError as e:
            time.sleep(10)
            last_error = str(e)
        except Exception as e:
            time.sleep(min(5 * (attempt + 1), MAX_RATE_LIMIT_SLEEP))
            last_error = str(e)

    raise Exception(f"All {retries} attempts failed. Last: {last_error}")


def call_groq_api(prompt, model=None, max_tokens=1500, retries=3):
    return call_ai_api(prompt, max_tokens=max_tokens, retries=retries)


def clean_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    for pattern in [r'```json\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        raw = m.group()
        try:
            return json.loads(raw)
        except Exception:
            depth = end = 0
            in_str = esc = False
            for i, ch in enumerate(raw):
                if esc:
                    esc = False
                    continue
                if ch == '\\' and in_str:
                    esc = True
                    continue
                if ch == '"':
                    in_str = not in_str
                if not in_str:
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
                except Exception:
                    pass
    m = re.search(r'\[[\s\S]*\]', text)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


def normalize_keys(obj):
    if isinstance(obj, dict):
        return {
            re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', k).lower().replace(' ', '_').replace('-', '_'):
            normalize_keys(v) for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [normalize_keys(i) for i in obj]
    return obj


# ─── FIX 2: Helper để ép item trong list strengths/weaknesses thành str ──────
def _coerce_str(item):
    """
    Strengths/weaknesses đôi khi là str, đôi khi là dict do model nhỏ trả sai schema.
    Hàm này chuẩn hóa về str an toàn.
    """
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Thử các key phổ biến theo thứ tự ưu tiên
        for key in ("name", "text", "description", "title", "value", "content"):
            if item.get(key):
                return str(item[key])
        # Fallback: ghép tất cả values
        return "; ".join(str(v) for v in item.values() if v)
    return str(item)


# ─── CAMELS SCORING ENGINE ───────────────────────────────────────────────────

def compute_camels_score(analysis):
    """
    CAMELS Rating System — chuẩn ngân hàng quốc tế:
    C-Capital, A-Assets, M-Management, E-Earnings, L-Liquidity, S-Sensitivity
    """
    products = analysis.get("products", [])
    digital = analysis.get("digital_capabilities", [])
    strategic = analysis.get("strategic_analysis", {})
    competitive = analysis.get("competitive_assessment", {})
    pricing = analysis.get("pricing", {})

    categories = {}
    for p in products:
        if isinstance(p, dict):
            cat = p.get("category", "OTHER")
            categories[cat] = categories.get(cat, 0) + 1

    n_digital = len(digital) if isinstance(digital, list) else 0
    n_promos = len(pricing.get("promotions", []))
    n_strengths = len(competitive.get("strengths", []))
    product_diversity = len(categories)

    # C — Capital: Investment + Savings product depth
    capital_score = min(10, 3 + (categories.get("INVESTMENT", 0) + categories.get("SAVINGS", 0)) * 1.2)
    # A — Asset Quality: Loan portfolio diversification
    asset_score = min(10, 2 + (categories.get("LOAN", 0) + categories.get("CARD", 0)) * 1.5)
    # M — Management: Strategic clarity
    mgmt_score = min(10, max(1,
        n_strengths * 0.8 +
        (2 if strategic.get("positioning") else 0) +
        (2 if strategic.get("value_proposition") else 0) +
        (1 if len(strategic.get("key_differentiators", [])) >= 3 else 0)
    ))
    # E — Earnings: Pricing power + promotions
    earn_score = min(10, 3 + n_promos * 0.7 + (2 if pricing.get("interest_rates") else 0))
    # L — Liquidity: Digital channels + payment products
    liquid_score = min(10, 2 + (categories.get("PAYMENT", 0) + categories.get("DIGITAL", 0)) * 1.0 + n_digital * 0.3)
    # S — Sensitivity: Market risk products (insurance, investment diversification)
    sens_score = min(10, 3 + (categories.get("INSURANCE", 0) + categories.get("INVESTMENT", 0)) * 1.2 + product_diversity * 0.4)

    overall = round((capital_score + asset_score + mgmt_score + earn_score + liquid_score + sens_score) / 6, 2)

    return {
        "capital_adequacy": round(capital_score, 1),
        "asset_quality": round(asset_score, 1),
        "management": round(mgmt_score, 1),
        "earnings": round(earn_score, 1),
        "liquidity": round(liquid_score, 1),
        "sensitivity": round(sens_score, 1),
        "overall": round(overall, 1),
        "product_diversity_index": product_diversity,
        "digital_maturity_index": round(min(10, n_digital * 1.2), 1),
    }


def compute_digital_maturity(analysis):
    """Digital Maturity Model (DMM) — 5 levels theo McKinsey Digital Banking framework"""
    digital = analysis.get("digital_capabilities", [])
    products = analysis.get("products", [])

    if isinstance(digital, list):
        digital_names = [
            (d.get("name", "") if isinstance(d, dict) else str(d)).lower()
            for d in digital
        ]
    else:
        digital_names = []

    digital_products = [
        p for p in products
        if isinstance(p, dict) and p.get("category") in ["DIGITAL", "PAYMENT"]
    ]

    has_mobile = any("app" in d or "mobile" in d for d in digital_names)
    has_open_api = any("api" in d or "open" in d for d in digital_names)
    has_ai = any(w in d for d in digital_names for w in ["ai", "ml", "chatbot", "robot", "voice"])
    has_biometric = any(w in d for d in digital_names for w in ["biometric", "face", "fingerprint", "vân tay"])
    has_qr = any("qr" in d or "scan" in d for d in digital_names)
    has_ekyc = any(w in d for d in digital_names for w in ["ekyc", "e-kyc", "định danh", "kyc"])

    omnichannel = min(10, len(digital_products) * 1.5 + (3 if has_mobile else 0))
    ai_personal = min(10, (5 if has_ai else 0) + (3 if has_biometric else 0) + (2 if has_ekyc else 0))
    payment_innov = min(10, (4 if has_qr else 0) + len([p for p in digital_products if "payment" in str(p).lower()]) * 1.5)
    open_platform = min(10, (6 if has_open_api else 0) + len(digital_names) * 0.5)
    data_analytics = min(10, (3 if has_ai else 0) + len(digital_names) * 0.4)

    maturity_score = round((omnichannel + ai_personal + payment_innov + open_platform + data_analytics) / 5, 1)

    if maturity_score >= 7.5:
        level, benchmark = "Level 5 — Digital Leader", "DBS, Nubank tier"
    elif maturity_score >= 6.0:
        level, benchmark = "Level 4 — Digital Accelerator", "Techcombank, VPBank tier"
    elif maturity_score >= 4.5:
        level, benchmark = "Level 3 — Digitally Enabled", "Mid-tier Vietnamese banks"
    elif maturity_score >= 3.0:
        level, benchmark = "Level 2 — Digital Initiator", "Traditional banks + digital add-ons"
    else:
        level, benchmark = "Level 1 — Digital Laggard", "Branch-centric legacy model"

    return {
        "overall_score": maturity_score,
        "level": level,
        "benchmark": benchmark,
        "dimensions": {
            "omnichannel_experience": round(omnichannel, 1),
            "ai_personalization": round(ai_personal, 1),
            "payment_innovation": round(payment_innov, 1),
            "open_platform_readiness": round(open_platform, 1),
            "data_analytics_capability": round(data_analytics, 1),
        },
        "key_features_detected": {
            "mobile_app": has_mobile,
            "open_banking_api": has_open_api,
            "ai_ml_features": has_ai,
            "biometric_auth": has_biometric,
            "qr_payments": has_qr,
            "ekyc": has_ekyc,
        }
    }


# ─── CHAIN-OF-THOUGHT EXTRACTION ─────────────────────────────────────────────

def run_chain_of_thought_extraction(text, entity_info, entity_type):
    """
    2-step CoT pipeline:
    Step 1 — Fast 8B model: raw product extraction
    Step 2 — Deep 70B model: strategic analysis & scoring
    """
    # ── Step 1: Fast Extraction ──────────────────────────────────────────
    step1_prompt = f"""Extract all financial products and services from this website content.
Entity: {entity_info['name']} ({entity_info['code']}) | Type: {entity_type}

WEBSITE DATA:
{text[:5500]}

Return JSON only:
{{
  "institution_type": "{entity_type}",
  "product_categories_found": ["CAT1"],
  "raw_products": [
    {{"name": "...", "category": "...", "price_info": "...", "features": ["..."], "target": "..."}}
  ],
  "pricing_signals": {{"rates": {{}}, "fees": [], "promotions": []}},
  "digital_signals": ["signal1"],
  "data_density": "high/medium/low",
  "key_messages": ["message1"]
}}"""

    print(f"  🔍 Step 1: Fast extraction...")
    step1_raw = call_ai_api(step1_prompt, max_tokens=2000,
                            system_prompt=EXPERT_EXTRACTION_SYSTEM,
                            tier="fast", temperature=0.05)
    step1 = clean_json(step1_raw) or {}

    # ── Step 2: Deep Strategic Analysis ──────────────────────────────────
    step2_prompt = f"""Deep strategic analysis of {entity_info['name']}.

STEP 1 EXTRACTION:
{json.dumps(step1, ensure_ascii=False)}

ADDITIONAL CONTEXT:
{text[5500:9000] if len(text) > 5500 else ""}

Perform McKinsey-level analysis. Return comprehensive JSON:
{{
  "entity_name": "{entity_info['name']}",
  "entity_code": "{entity_info['code']}",
  "entity_type": "{entity_type}",
  "website": "",
  "products": [
    {{
      "category": "CATEGORY_CODE",
      "name": "Specific product name",
      "features": ["Feature 1", "Feature 2"],
      "target": "Target segment",
      "highlight": "Key selling point",
      "price_signal": "Rate or fee if found"
    }}
  ],
  "pricing": {{
    "interest_rates": {{"savings_rate": "X%", "loan_rate": "X%"}},
    "fees": ["Fee 1"],
    "promotions": [
      {{"name": "...", "benefit": "...", "target_segment": "...", "validity": "..."}}
    ],
    "pricing_philosophy": "Value/Premium/Competitive/Discount"
  }},
  "digital_capabilities": [
    {{"name": "Feature", "description": "What it does", "maturity": "Basic/Advanced/Best-in-class"}}
  ],
  "strategic_analysis": {{
    "positioning": "Specific positioning from data",
    "target_segments": ["Segment 1", "Segment 2"],
    "key_differentiators": ["Differentiator 1", "Differentiator 2"],
    "value_proposition": "Core value prop",
    "pricing_strategy": "Specific pricing strategy",
    "distribution_strategy": "Channel mix",
    "marketing_approach": "Key marketing approach",
    "growth_vectors": ["Growth vector 1"],
    "strategic_gaps": ["Gap vs best practice 1"]
  }},
  "competitive_assessment": {{
    "strengths": ["Strength 1", "Strength 2"],
    "weaknesses": ["Weakness 1"],
    "market_position": "Leader/Challenger/Follower/Niche",
    "competitive_threat_level": "High/Medium/Low",
    "unique_selling_points": ["USP 1"],
    "benchmark_vs_best": "Comparison to Techcombank/VCB/VPBank"
  }},
  "data_confidence": "high/medium/low",
  "data_notes": "Data quality notes"
}}"""

    print(f"  🧠 Step 2: Deep strategic analysis (70B)...")
    step2_raw = call_ai_api(step2_prompt, max_tokens=3500,
                            system_prompt=EXPERT_BANKING_SYSTEM,
                            tier="ultra", temperature=0.12)
    result = clean_json(step2_raw)

    if result:
        # Inject step1 pricing if missing
        if not result.get("pricing", {}).get("interest_rates") and step1.get("pricing_signals", {}).get("rates"):
            result.setdefault("pricing", {})["interest_rates"] = step1["pricing_signals"]["rates"]
        print(f"  ✅ CoT done: {len(result.get('products', []))} products extracted")
    else:
        print(f"  ⚠️ Step 2 failed — using step 1 fallback")
        result = {
            "entity_name": entity_info['name'],
            "entity_code": entity_info['code'],
            "entity_type": entity_type,
            "products": step1.get("raw_products", []),
            "pricing": {
                "interest_rates": step1.get("pricing_signals", {}).get("rates", {}),
                "fees": step1.get("pricing_signals", {}).get("fees", []),
                "promotions": step1.get("pricing_signals", {}).get("promotions", []),
            },
            "digital_capabilities": [{"name": s, "description": ""} for s in step1.get("digital_signals", [])],
            "strategic_analysis": {
                "positioning": "; ".join(step1.get("key_messages", [])[:2]),
                "target_segments": [],
                "key_differentiators": step1.get("key_messages", [])[:3],
            },
            "competitive_assessment": {
                "strengths": [], "weaknesses": [],
                "market_position": "Unknown",
                "competitive_threat_level": "Medium",
            },
            "data_confidence": step1.get("data_density", "low"),
            "data_notes": "Deep analysis failed; using fast extraction only",
        }

    return result


# ─── MASTER STRATEGY ANALYSIS ────────────────────────────────────────────────

def analyze_strategy(results):
    """Master competitive strategy analysis — Board-level McKinsey output."""
    if not results:
        return {
            "executive_summary": "Không có dữ liệu để phân tích.",
            "competitive_ranking": [],
            "strategic_recommendations": {"overall_strategy": "N/A"}
        }

    # ── Enrich with CAMELS + Digital Maturity scores ──────────────────────
    enriched = []
    for r in results:
        a = r.get("analysis", {})
        camels = compute_camels_score(a)
        digital = compute_digital_maturity(a)

        products = a.get("products", [])
        prod_by_cat = {}
        prod_names = []
        for p in products:
            if isinstance(p, dict):
                cat = p.get("category", "OTHER")
                prod_by_cat.setdefault(cat, []).append(p.get("name", ""))
                label = f"{cat}:{p.get('name','')}"
                if p.get("highlight"):
                    label += f" [{p['highlight'][:35]}]"
                prod_names.append(label)
            elif isinstance(p, str):
                prod_names.append(p)

        strategic = a.get("strategic_analysis", {})
        competitive = a.get("competitive_assessment", {})
        pricing = a.get("pricing", {})

        enriched.append({
            "entity": a.get("entity_name", a.get("bank_name", "Unknown")),
            "code": a.get("entity_code", a.get("bank_code", "")),
            "type": r.get("entity_type", "company"),
            "camels_scores": camels,
            "digital_maturity": digital,
            "product_count": len(products),
            "product_categories": list(prod_by_cat.keys()),
            "top_products": prod_names[:20],
            "products_by_category": {k: v[:5] for k, v in prod_by_cat.items()},
            "digital_count": len(a.get("digital_capabilities", [])),
            "key_digital_features": [
                (d.get("name") if isinstance(d, dict) else d)
                for d in a.get("digital_capabilities", [])[:10] if d
            ],
            "positioning": strategic.get("positioning", "")[:200],
            "value_proposition": strategic.get("value_proposition", "")[:150],
            "growth_vectors": strategic.get("growth_vectors", [])[:3],
            "strategic_gaps": strategic.get("strategic_gaps", [])[:3],
            "target_segments": strategic.get("target_segments", [])[:4],
            "key_differentiators": strategic.get("key_differentiators", [])[:4],
            "strengths": competitive.get("strengths", [])[:4],
            "weaknesses": competitive.get("weaknesses", [])[:3],
            "unique_selling_points": competitive.get("unique_selling_points", [])[:3],
            "market_position": competitive.get("market_position", ""),
            "threat_level": competitive.get("competitive_threat_level", ""),
            "benchmark_vs_best": competitive.get("benchmark_vs_best", ""),
            "pricing_philosophy": pricing.get("pricing_philosophy", ""),
            "interest_rates": a.get("interest_rates", pricing.get("interest_rates", {})),
            "promotions_count": len(a.get("promotions", pricing.get("promotions", []))),
            "data_confidence": a.get("data_confidence", "medium"),
            "extraction_quality": r.get("extraction_quality", "limited"),
        })

    n = len(enriched)
    types = list(set(s.get("type") for s in enriched))
    ctx = "ngân hàng/tổ chức tài chính" if "bank" in types else "công ty/tổ chức"

    prompt = f"""You are a Senior Strategy Partner presenting to the Board of Directors.
Vietnam Financial Services | {n} {ctx} analyzed

ENRICHED DATA (with CAMELS + Digital Maturity pre-computed):
{json.dumps(enriched, ensure_ascii=False, indent=2)}

Deliver a deep competitive intelligence report. Return ONLY this JSON:
{{
  "executive_summary": "4-5 sentence board-level insight: who is winning WHY (with specific evidence), critical battleground, most important strategic finding. Reference specific scores/products.",

  "market_overview": {{
    "total_entities_analyzed": {n},
    "market_dynamics": "Specific competitive dynamics from data",
    "key_trends": ["Data-backed trend 1", "Trend 2", "Trend 3"],
    "disruption_factors": ["Specific disruption risk 1", "Factor 2"],
    "critical_battleground": "Single most contested dimension"
  }},

  "competitive_ranking": [
    {{
      "rank": 1,
      "entity": "Entity name",
      "position": "Specific market position",
      "score": "8.5",
      "camels_overall": "7.2",
      "digital_maturity_level": "Level 4 — Digital Accelerator",
      "key_strength": "Most impactful strength with evidence",
      "key_weakness": "Most critical weakness",
      "analysis": "2-3 sentences on competitive position and trajectory"
    }}
  ],

  "detailed_competitor_analysis": [
    {{
      "entity": "Entity name",
      "entity_type": "bank/fintech/insurance",
      "camels_profile": {{
        "capital_adequacy": 7, "asset_quality": 6, "management": 8,
        "earnings": 7, "liquidity": 7, "sensitivity": 6, "overall": 6.8
      }},
      "digital_maturity": {{
        "overall_score": 7.2,
        "level": "Level 4 — Digital Accelerator",
        "strongest_dimension": "Which dimension leads",
        "biggest_gap": "Which dimension lags"
      }},
      "product_strategy": "Product portfolio assessment: breadth vs. focus, mass vs. premium",
      "pricing_strategy": "Specific pricing observations",
      "distribution_strategy": "Channel mix and digital-physical balance",
      "digital_strategy": "Specific digital capabilities and maturity",
      "target_customer": "Primary customer segment(s)",
      "competitive_score": {{
        "product_breadth": 7, "digital_capability": 8, "pricing_competitiveness": 7,
        "brand_strength": 8, "customer_experience": 7, "innovation": 6, "overall": 7
      }},
      "key_threats": ["Specific threat 1", "Threat 2"],
      "key_opportunities": ["Specific opportunity 1", "Opportunity 2"],
      "strategic_verdict": "2-sentence strategic assessment"
    }}
  ],

  "product_comparison_matrix": {{
    "Danh mục Sản phẩm": {{"leader": "...", "ranking": ["1st: ...", "2nd: ..."], "gap_analysis": "..."}},
    "Năng lực Digital": {{"leader": "...", "ranking": ["1st: ...", "2nd: ..."], "gap_analysis": "..."}},
    "Chiến lược Giá": {{"leader": "...", "ranking": ["1st: ...", "2nd: ..."], "gap_analysis": "..."}},
    "Phân khúc KH": {{"leader": "...", "ranking": ["1st: ...", "2nd: ..."], "gap_analysis": "..."}},
    "Đổi mới sáng tạo": {{"leader": "...", "ranking": ["1st: ...", "2nd: ..."], "gap_analysis": "..."}}
  }},

  "strategic_recommendations": {{
    "overall_strategy": "Single most important strategic imperative",
    "product_strategy": "Specific product moves: build/buy/kill",
    "pricing_strategy": "Specific pricing repositioning",
    "distribution_strategy": "Channel optimization",
    "digital_strategy": "3-step digital transformation roadmap",
    "quick_wins": [
      "0-30 days: Specific action + expected outcome",
      "30-60 days: Specific action",
      "60-90 days: Specific action"
    ],
    "implementation_roadmap": [
      {{
        "phase": "Phase 1: Foundation (Q1-Q2)",
        "objective": "Specific measurable objective",
        "actions": ["Concrete action 1", "Action 2", "Action 3"],
        "milestones": "KPI: [metric] = [target] by [date]",
        "investment_required": "Resource estimate"
      }},
      {{
        "phase": "Phase 2: Acceleration (Q3-Q4)",
        "objective": "Objective",
        "actions": ["Action 1", "Action 2"],
        "milestones": "KPIs",
        "investment_required": "Resources"
      }},
      {{
        "phase": "Phase 3: Leadership (Year 2)",
        "objective": "Long-term goal",
        "actions": ["Action 1", "Action 2"],
        "milestones": "Long-term KPIs",
        "investment_required": "Investment level"
      }}
    ]
  }},

  "market_opportunities": [
    {{
      "opportunity": "Specific opportunity",
      "rationale": "Gap in competitive landscape",
      "potential_impact": "Quantified impact",
      "difficulty": "Easy/Medium/Hard",
      "priority": "High/Medium/Low",
      "time_to_capture": "Timeline",
      "who_should_pursue": "Best positioned entity type"
    }}
  ],

  "risk_mitigation": [
    {{
      "risk": "Specific risk",
      "probability": "High/Medium/Low",
      "impact": "High/Medium/Low",
      "risk_score": "H/M/L",
      "mitigation": "Specific mitigation action"
    }}
  ],

  "competitive_intelligence_summary": {{
    "biggest_winner": "Entity + specific reasons",
    "biggest_threat": "Entity + why dangerous",
    "hidden_gem": "Underrated entity + specific potential",
    "key_battleground": "Critical competitive dimension",
    "strategic_imperative": "Single most important action in next 6 months"
  }},

  "camels_leaderboard": [
    {{
      "entity": "Entity name",
      "camels_overall": 7.5,
      "digital_maturity": 6.8,
      "composite_score": 7.2,
      "strategic_tier": "Tier 1 Leader / Tier 2 Challenger / Tier 3 Follower"
    }}
  ]
}}"""

    try:
        print("\n🎯 Master Strategy Analysis (70B deep reasoning)...")
        content = call_ai_api(prompt, max_tokens=4000, retries=4,
                              system_prompt=EXPERT_STRATEGY_SYSTEM,
                              tier="ultra", temperature=0.1)
        strategy = clean_json(content)
        if not strategy:
            raise Exception("Cannot parse strategy JSON")

        # Always inject computed scores into leaderboard
        leaderboard = []
        for s in enriched:
            cam = s.get("camels_scores", {})
            dig = s.get("digital_maturity", {})
            c_score = cam.get("overall", 5.0)
            d_score = dig.get("overall_score", 5.0)
            comp = round(c_score * 0.6 + d_score * 0.4, 2)
            tier_label = ("Tier 1 — Leader" if comp >= 7 else
                          "Tier 2 — Challenger" if comp >= 5 else "Tier 3 — Follower")
            leaderboard.append({
                "entity": s["entity"],
                "camels_overall": c_score,
                "digital_maturity": d_score,
                "digital_level": dig.get("level", ""),
                "composite_score": comp,
                "strategic_tier": tier_label,
                "camels_breakdown": cam,
                "digital_dimensions": dig.get("dimensions", {}),
                "digital_features": dig.get("key_features_detected", {}),
            })

        strategy["camels_leaderboard"] = leaderboard
        return normalize_keys(strategy)

    except Exception as e:
        print(f"❌ Master strategy failed: {str(e)}")
        return {
            "executive_summary": f"Lỗi phân tích: {str(e)[:200]}. Vui lòng kiểm tra API key và thử lại.",
            "market_overview": {"total_entities_analyzed": n},
            "competitive_ranking": [
                {
                    "rank": i + 1,
                    "entity": s.get("entity", ""),
                    "position": s.get("market_position", "N/A"),
                    "score": str(s.get("camels_scores", {}).get("overall", "N/A")),
                    # ─── FIX 2: dùng _coerce_str để xử lý strengths dạng dict ───
                    "key_strength": ", ".join(
                        _coerce_str(x) for x in s.get("strengths", [])[:1]
                    ),
                    "analysis": s.get("positioning", ""),
                }
                for i, s in enumerate(enriched)
            ],
            "camels_leaderboard": [
                {
                    "entity": s["entity"],
                    "camels_overall": s.get("camels_scores", {}).get("overall", 0),
                    "digital_maturity": s.get("digital_maturity", {}).get("overall_score", 0),
                    "composite_score": round(
                        s.get("camels_scores", {}).get("overall", 0) * 0.6 +
                        s.get("digital_maturity", {}).get("overall_score", 0) * 0.4, 2
                    ),
                    "strategic_tier": "Unknown",
                    "camels_breakdown": s.get("camels_scores", {}),
                    "digital_dimensions": s.get("digital_maturity", {}).get("dimensions", {}),
                }
                for s in enriched
            ],
            "strategic_recommendations": {"overall_strategy": "Không thể tổng hợp — vui lòng thử lại."}
        }
