"""
╔══════════════════════════════════════════════════════════════╗
║  DEEP DATA EXTRACTION ENGINE v3.0                           ║
║  Chain-of-Thought | CAMELS-enriched | International Std.    ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import re
from llm import (
    call_ai_api, clean_json,
    run_chain_of_thought_extraction,
    compute_camels_score, compute_digital_maturity,
    EXPERT_EXTRACTION_SYSTEM,
)


# ─── ENTITY RECOGNITION ──────────────────────────────────────────────────────

KNOWN_ENTITIES = {
    # Big 4 State Banks
    'vietcombank': {'name': 'Vietcombank', 'code': 'VCB', 'type': 'bank', 'tier': 'Big4'},
    'vietinbank': {'name': 'VietinBank', 'code': 'CTG', 'type': 'bank', 'tier': 'Big4'},
    'bidv': {'name': 'BIDV', 'code': 'BIDV', 'type': 'bank', 'tier': 'Big4'},
    'agribank': {'name': 'Agribank', 'code': 'AGB', 'type': 'bank', 'tier': 'Big4'},
    # Major Private Banks
    'techcombank': {'name': 'Techcombank', 'code': 'TCB', 'type': 'bank', 'tier': 'Tier1'},
    'vpbank': {'name': 'VPBank', 'code': 'VPB', 'type': 'bank', 'tier': 'Tier1'},
    'mbbank': {'name': 'MB Bank', 'code': 'MBB', 'type': 'bank', 'tier': 'Tier1'},
    'mb.com': {'name': 'MB Bank', 'code': 'MBB', 'type': 'bank', 'tier': 'Tier1'},
    'acb': {'name': 'ACB', 'code': 'ACB', 'type': 'bank', 'tier': 'Tier1'},
    'sacombank': {'name': 'Sacombank', 'code': 'STB', 'type': 'bank', 'tier': 'Tier1'},
    'hdbank': {'name': 'HDBank', 'code': 'HDB', 'type': 'bank', 'tier': 'Tier2'},
    'tpbank': {'name': 'TPBank', 'code': 'TPB', 'type': 'bank', 'tier': 'Tier2'},
    'vib': {'name': 'VIB', 'code': 'VIB', 'type': 'bank', 'tier': 'Tier2'},
    'msb': {'name': 'MSB', 'code': 'MSB', 'type': 'bank', 'tier': 'Tier2'},
    'ocb': {'name': 'OCB', 'code': 'OCB', 'type': 'bank', 'tier': 'Tier2'},
    'seabank': {'name': 'SeABank', 'code': 'SSB', 'type': 'bank', 'tier': 'Tier2'},
    'abbank': {'name': 'ABBank', 'code': 'ABB', 'type': 'bank', 'tier': 'Tier2'},
    'bacabank': {'name': 'BacABank', 'code': 'BAB', 'type': 'bank', 'tier': 'Tier2'},
    'lpbank': {'name': 'LPBank', 'code': 'LPB', 'type': 'bank', 'tier': 'Tier2'},
    'pvcombank': {'name': 'PVcomBank', 'code': 'PVC', 'type': 'bank', 'tier': 'Tier2'},
    'eximbank': {'name': 'Eximbank', 'code': 'EIB', 'type': 'bank', 'tier': 'Tier2'},
    'ncb': {'name': 'NCB', 'code': 'NCB', 'type': 'bank', 'tier': 'Tier3'},
    'kienlongbank': {'name': 'KienlongBank', 'code': 'KLB', 'type': 'bank', 'tier': 'Tier3'},
    'namabank': {'name': 'Nam A Bank', 'code': 'NAB', 'type': 'bank', 'tier': 'Tier3'},
    # Foreign Banks
    'shinhan': {'name': 'Shinhan Bank VN', 'code': 'SHB_VN', 'type': 'bank', 'tier': 'Foreign'},
    'hsbc': {'name': 'HSBC Vietnam', 'code': 'HSBC', 'type': 'bank', 'tier': 'Foreign'},
    'citibank': {'name': 'Citibank Vietnam', 'code': 'CITI', 'type': 'bank', 'tier': 'Foreign'},
    'standardchartered': {'name': 'Standard Chartered VN', 'code': 'SCB', 'type': 'bank', 'tier': 'Foreign'},
    'woori': {'name': 'Woori Bank VN', 'code': 'WB_VN', 'type': 'bank', 'tier': 'Foreign'},
    'uob': {'name': 'UOB Vietnam', 'code': 'UOB', 'type': 'bank', 'tier': 'Foreign'},
    # Fintech / E-wallets
    'momo': {'name': 'MoMo', 'code': 'MOMO', 'type': 'fintech', 'tier': 'Super-app'},
    'zalopay': {'name': 'ZaloPay', 'code': 'ZLP', 'type': 'fintech', 'tier': 'Super-app'},
    'vnpay': {'name': 'VNPAY', 'code': 'VNP', 'type': 'fintech', 'tier': 'Payment'},
    'payoo': {'name': 'Payoo', 'code': 'PAY', 'type': 'fintech', 'tier': 'Payment'},
    'shopeepay': {'name': 'ShopeePay', 'code': 'SPP', 'type': 'fintech', 'tier': 'Payment'},
    'timo': {'name': 'Timo', 'code': 'TIMO', 'type': 'fintech', 'tier': 'Neobank'},
    'cake': {'name': 'CAKE by VPBank', 'code': 'CAKE', 'type': 'fintech', 'tier': 'Neobank'},
    'tnex': {'name': 'TNEX', 'code': 'TNEX', 'type': 'fintech', 'tier': 'Neobank'},
    # Insurance
    'baoviet': {'name': 'Bảo Việt', 'code': 'BVH', 'type': 'insurance', 'tier': 'Tier1'},
    'baoviethealthcare': {'name': 'Bảo Việt Healthcare', 'code': 'BVH', 'type': 'insurance', 'tier': 'Tier1'},
    'prudential': {'name': 'Prudential Vietnam', 'code': 'PRU', 'type': 'insurance', 'tier': 'Foreign'},
    'manulife': {'name': 'Manulife Vietnam', 'code': 'MFC', 'type': 'insurance', 'tier': 'Foreign'},
    'aia': {'name': 'AIA Vietnam', 'code': 'AIA', 'type': 'insurance', 'tier': 'Foreign'},
    'sunlife': {'name': 'Sun Life Vietnam', 'code': 'SLF', 'type': 'insurance', 'tier': 'Foreign'},
    'generali': {'name': 'Generali Vietnam', 'code': 'GEN', 'type': 'insurance', 'tier': 'Foreign'},
    'pvi': {'name': 'PVI Insurance', 'code': 'PVI', 'type': 'insurance', 'tier': 'Tier1'},
}


def get_entity_info(url):
    """Identify entity from URL with tier classification."""
    url_lower = url.lower()
    for key, info in KNOWN_ENTITIES.items():
        if key in url_lower:
            return info

    # Auto-parse domain
    try:
        domain = url.split("//")[-1].split("/")[0].replace("www.", "").replace("www2.", "")
        name_raw = domain.split(".")[0]
        name = name_raw.upper()
        entity_type = 'company'
        if any(w in url_lower for w in ['bank', 'ngan-hang', 'financial', 'finance', 'vib', 'acb', 'msb']):
            entity_type = 'bank'
        elif any(w in url_lower for w in ['insurance', 'bao-hiem', 'life', 'assurance', 'baoviet']):
            entity_type = 'insurance'
        elif any(w in url_lower for w in ['pay', 'wallet', 'fintech', 'ví', 'momo', 'zalo']):
            entity_type = 'fintech'
        return {'name': name, 'code': name[:4].upper(), 'type': entity_type, 'tier': 'Unknown'}
    except Exception:
        return {'name': 'UNKNOWN', 'code': 'UNK', 'type': 'company', 'tier': 'Unknown'}


# ─── CATEGORY GUIDES ─────────────────────────────────────────────────────────

CATEGORY_GUIDES = {
    "bank": """
Standard banking product categories (MUST use these codes):
- SAVINGS: Tiết kiệm, gửi tiền, tài khoản tiết kiệm, tiền gửi có kỳ hạn, online savings
- LOAN: Vay cá nhân, vay mua nhà, vay mua xe, vay tiêu dùng, tín dụng, BNPL
- CARD: Thẻ tín dụng, thẻ ghi nợ, thẻ trả trước, Visa/Mastercard/JCB/Amex
- DIGITAL: Mobile banking app, Internet banking, eKYC, digital onboarding, chatbot
- INSURANCE: Bảo hiểm nhân thọ, bảo hiểm sức khỏe, bảo hiểm khoản vay, bancassurance
- INVESTMENT: Quỹ đầu tư, trái phiếu, chứng khoán, vàng, gold savings
- PAYMENT: Chuyển tiền, thanh toán hóa đơn, nạp tiền điện thoại, QR payment, SWIFT
- BUSINESS: Tài khoản doanh nghiệp, vay doanh nghiệp, L/C, trade finance, payroll
- WEALTH: Private banking, wealth management, portfolio management, high net worth
- OTHER: Khác""",
    "fintech": """
Fintech/E-wallet product categories:
- PAYMENT: Thanh toán QR, chuyển tiền, nạp tiền, thanh toán hóa đơn, top-up
- SAVINGS: Tiết kiệm số, tích lũy, heo đất, staking
- LOAN: Vay tiêu dùng, BNPL (mua trước trả sau), tín dụng vi mô
- INVESTMENT: Đầu tư, mua vàng, quỹ, stocks
- CASHBACK: Hoàn tiền, cashback, điểm thưởng, loyalty
- MERCHANT: Giải pháp merchant, POS, QR merchant, business tools
- INSURANCE: Bảo hiểm vi mô, bảo hiểm sức khỏe mini
- DIGITAL: Super app features, AI assistant, open banking integration
- OTHER: Other services""",
    "insurance": """
Insurance product categories:
- LIFE: Bảo hiểm nhân thọ, tử kỳ, trọn đời, endowment
- HEALTH: Bảo hiểm sức khỏe, y tế, tai nạn, ung thư, critical illness
- INVESTMENT: Bảo hiểm liên kết đầu tư (unit-linked), bảo hiểm hỗn hợp
- SAVINGS: Bảo hiểm tiết kiệm, giáo dục, hưu trí
- NON_LIFE: Bảo hiểm xe cộ, tài sản, du lịch, hàng hóa, nhà ở
- BUSINESS: Bảo hiểm doanh nghiệp, trách nhiệm, D&O, property all-risk
- DIGITAL: Digital insurance, usage-based, on-demand, telematics
- OTHER: Other insurance products""",
    "company": """
General company product categories:
- PRODUCT: Core products
- SERVICE: Core services
- SUBSCRIPTION: Subscription plans, SaaS tiers
- SOLUTION: Enterprise solutions, B2B
- SUPPORT: Support, warranty, after-sales
- DIGITAL: Digital products, apps, platforms
- OTHER: Other"""
}


def extract_data(text, url):
    """
    Main extraction pipeline with Chain-of-Thought deep reasoning.
    Uses 2-step CoT: fast extraction → deep strategic analysis.
    """
    entity_info = get_entity_info(url)

    if not text or len(text) < 100:
        return create_error_response(entity_info, url, "Không crawl được dữ liệu từ website")

    source_type = "live_crawl_requests" if "SOURCE: live_crawl_requests" in text else "live_crawl"
    entity_type = entity_info.get('type', 'company')

    print(f"\n{'='*55}")
    print(f"🏦 Deep extraction: {entity_info['name']} ({entity_info.get('tier','?')}) | {entity_type}")
    print(f"   Data: {len(text)} chars | Source: {source_type}")

    try:
        # Run Chain-of-Thought 2-step extraction
        parsed = run_chain_of_thought_extraction(text, entity_info, entity_type)

        # Normalize and enrich
        parsed.setdefault("entity_name", entity_info['name'])
        parsed.setdefault("entity_code", entity_info['code'])
        parsed.setdefault("entity_type", entity_type)
        parsed.setdefault("products", [])
        parsed.setdefault("pricing", {"promotions": [], "fees": [], "interest_rates": {}})
        parsed.setdefault("digital_capabilities", [])
        parsed.setdefault("strategic_analysis", {})
        parsed.setdefault("competitive_assessment", {})
        parsed.setdefault("data_confidence", "medium")

        # Add tier info
        parsed["entity_tier"] = entity_info.get("tier", "Unknown")

        # Backward compat
        parsed["bank_name"] = parsed["entity_name"]
        parsed["bank_code"] = parsed["entity_code"]
        parsed["promotions"] = parsed.get("pricing", {}).get("promotions", [])
        parsed["interest_rates"] = parsed.get("pricing", {}).get("interest_rates", {})

        # Normalize digital_capabilities
        dc = parsed.get("digital_capabilities", [])
        if dc and isinstance(dc[0], dict):
            parsed["digital_capabilities_detailed"] = dc
            parsed["digital_capabilities"] = [d.get("name", "") for d in dc if d.get("name")]
        else:
            parsed["digital_capabilities_detailed"] = [{"name": d, "description": ""} for d in dc]

        # Compute scores
        camels = compute_camels_score(parsed)
        digital_maturity = compute_digital_maturity(parsed)
        parsed["camels_scores"] = camels
        parsed["digital_maturity_scores"] = digital_maturity

        # Quality assessment
        n_products = len(parsed.get("products", []))
        confidence = parsed.get("data_confidence", "medium")

        if n_products >= 10 and confidence == "high":
            quality = "deep"
        elif n_products >= 5:
            quality = "good"
        elif n_products >= 2:
            quality = "limited"
        else:
            quality = "limited"

        print(f"  ✅ Complete: {n_products} products | quality={quality} | "
              f"CAMELS={camels['overall']} | Digital={digital_maturity['overall_score']}")

        return {
            "url": url,
            "analysis": parsed,
            "extraction_quality": quality,
            "source": source_type,
            "entity_type": entity_type,
            "entity_tier": entity_info.get("tier", "Unknown"),
        }

    except Exception as e:
        print(f"  ❌ Extraction failed: {str(e)}")
        return create_error_response(entity_info, url, str(e))


def extract_data_single_step(text, url):
    """
    Single-step extraction for file uploads and lighter tasks.
    Uses fast model with rich category guide.
    """
    entity_info = get_entity_info(url)
    entity_type = entity_info.get('type', 'company')
    category_guide = CATEGORY_GUIDES.get(entity_type, CATEGORY_GUIDES["company"])

    prompt = f"""Extract all products/services from this {entity_type} data.
Entity: {entity_info['name']} ({entity_info['code']})

{category_guide}

DATA:
{text[:8000]}

Return comprehensive JSON:
{{
  "entity_name": "{entity_info['name']}",
  "entity_code": "{entity_info['code']}",
  "entity_type": "{entity_type}",
  "products": [
    {{
      "category": "CATEGORY_CODE",
      "name": "Product name from data",
      "features": ["Feature 1"],
      "target": "Target segment",
      "highlight": "Key selling point"
    }}
  ],
  "pricing": {{
    "interest_rates": {{}},
    "fees": [],
    "promotions": [{{"name": "...", "benefit": "...", "target_segment": "...", "validity": ""}}]
  }},
  "digital_capabilities": [{{"name": "...", "description": ""}}],
  "strategic_analysis": {{
    "positioning": "...",
    "target_segments": [],
    "key_differentiators": [],
    "value_proposition": "..."
  }},
  "competitive_assessment": {{
    "strengths": [],
    "weaknesses": [],
    "market_position": "Leader/Challenger/Follower/Niche",
    "competitive_threat_level": "High/Medium/Low",
    "unique_selling_points": []
  }},
  "data_confidence": "high/medium/low"
}}"""

    raw = call_ai_api(prompt, max_tokens=3000,
                      system_prompt=EXPERT_EXTRACTION_SYSTEM,
                      tier="auto", temperature=0.1)
    return clean_json(raw)


def create_error_response(entity_info, url="", error_msg=""):
    return {
        "url": url,
        "analysis": {
            "entity_name": entity_info['name'],
            "entity_code": entity_info['code'],
            "entity_type": entity_info.get('type', 'company'),
            "entity_tier": entity_info.get('tier', 'Unknown'),
            "bank_name": entity_info['name'],
            "bank_code": entity_info['code'],
            "products": [],
            "interest_rates": {},
            "promotions": [],
            "digital_capabilities": [],
            "digital_capabilities_detailed": [],
            "camels_scores": {
                "capital_adequacy": 0, "asset_quality": 0, "management": 0,
                "earnings": 0, "liquidity": 0, "sensitivity": 0, "overall": 0
            },
            "digital_maturity_scores": {"overall_score": 0, "level": "Unknown"},
            "strategic_analysis": {
                "positioning": "Không thể phân tích",
                "target_segments": [],
                "key_differentiators": [],
                "pricing_strategy": "Unknown",
                "distribution_strategy": "Unknown",
            },
            "competitive_assessment": {
                "strengths": [],
                "weaknesses": [error_msg or "Website không khả dụng"],
                "market_position": "Unknown",
                "competitive_threat_level": "Unknown",
            },
            "data_confidence": "none",
            "data_notes": error_msg,
        },
        "extraction_quality": "error",
        "source": "error",
        "entity_type": entity_info.get('type', 'company'),
        "entity_tier": entity_info.get('tier', 'Unknown'),
    }
