"""
╔══════════════════════════════════════════════════════════════════╗
║  GLOBAL BANKING INTELLIGENCE ENGINE v7.0                        ║
║  Deep AI · Basel III/IV · CAMELS · VaR · Stress Test · ESG     ║
║  Powered by Groq API (FREE) — llama-3.3-70b / DeepSeek / Gemma ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, json, re, requests, time, random
from datetime import datetime

# ─── GROQ FREE MODELS (strongest → fallback) ───────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = [
    "llama-3.3-70b-versatile",      # Best reasoning
    "llama-3.1-70b-versatile",      # Strong fallback
    "deepseek-r1-distill-llama-70b",# Deep reasoning
    "llama-3.1-8b-instant",         # Fast fallback
    "gemma2-9b-it",                 # Final fallback
]

BANKING_SYSTEM_PROMPT = """You are an elite Institutional Banking AI — equivalent to:
• Goldman Sachs Global Investment Research team
• McKinsey Financial Institutions Practice
• BlackRock Aladdin Risk Engine
• Federal Reserve DFAST stress test team
• Basel Committee on Banking Supervision analysts

MANDATORY OUTPUT RULES:
1. Return ONLY pure valid JSON — no markdown fences, no preamble text, no explanation
2. All keys in snake_case
3. Numbers as numeric types (not strings), percentages as decimals (0.15 = 15%)
4. Never fabricate exact figures you can't infer — mark uncertain values with "estimated" prefix
5. Apply rigorous financial reasoning with cause-and-effect logic"""


# ══════════════════════════════════════════════════════════════════
#  CORE GROQ CALLER — smart retry + model rotation (free tier)
# ══════════════════════════════════════════════════════════════════
def call_ai_api(prompt, max_tokens=3500, retries=6, system_override=None):
    system = system_override or BANKING_SYSTEM_PROMPT
    api_key = os.environ.get("GROQ_API_KEY_BK")
    if not api_key:
        raise Exception("GROQ_API_KEY_BK not set in environment variables")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_error = None

    for attempt in range(retries):
        model = GROQ_MODELS[attempt % len(GROQ_MODELS)]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "top_p": 0.9,
        }
        try:
            print(f"🤖 Groq [{model}] attempt {attempt+1}/{retries}…")
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=90)

            if res.status_code == 429:
                retry_after = int(res.headers.get("Retry-After", 0))
                wait = max(retry_after, 12 * (attempt + 1))
                print(f"⏳ Rate-limited [{model}], wait {wait}s, switching model…")
                time.sleep(wait); last_error = "rate_limit"; continue

            if res.status_code in (400, 404):
                err = (res.json().get("error", {}) if res.content else {}).get("message", "")
                print(f"⚠️  Model {model} error {res.status_code}: {err}")
                last_error = f"model_error_{model}"; time.sleep(2); continue

            if res.status_code == 503:
                wait = 15 * (attempt + 1)
                print(f"⏳ Service unavailable, waiting {wait}s…")
                time.sleep(wait); last_error = "service_unavailable"; continue

            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"].strip()
            content = _strip_fences(content)
            print(f"✅ Groq OK [{model}] ({len(content)} chars)")
            return content

        except requests.exceptions.Timeout:
            wait = 8 * (attempt + 1)
            print(f"⏱️  Timeout [{model}], wait {wait}s…")
            time.sleep(wait); last_error = "timeout"
        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"❌ Error [{model}]: {str(e)[:80]}, wait {wait}s…")
            time.sleep(wait); last_error = str(e)

    raise Exception(f"Groq API failed after {retries} attempts. Last: {last_error}")


def _strip_fences(text):
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*',     '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$',     '', text, flags=re.MULTILINE)
    return text.strip()

# backward-compat alias
call_groq_api = call_ai_api


# ══════════════════════════════════════════════════════════════════
#  JSON UTILS
# ══════════════════════════════════════════════════════════════════
def clean_json(text):
    if not text: return None
    try: return json.loads(text)
    except: pass
    for pat in [r'```json\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try: return json.loads(m.group(1))
            except: pass
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        raw = m.group()
        try: return json.loads(raw)
        except:
            depth = 0; end = 0; in_str = False; esc = False
            for i, ch in enumerate(raw):
                if esc: esc = False; continue
                if ch == '\\' and in_str: esc = True; continue
                if ch == '"' and not esc: in_str = not in_str
                if not in_str:
                    if ch == '{': depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0: end = i + 1; break
            if end:
                try: return json.loads(raw[:end])
                except: pass
    m = re.search(r'\[[\s\S]*\]', text)
    if m:
        try: return json.loads(m.group())
        except: pass
    return None

def normalize_keys(obj):
    if isinstance(obj, dict):
        return {re.sub(r'(?<=[a-z0-9])(?=[A-Z])','_',k).lower()
                  .replace(' ','_').replace('-','_'): normalize_keys(v)
                for k, v in obj.items()}
    if isinstance(obj, list): return [normalize_keys(i) for i in obj]
    return obj


# ══════════════════════════════════════════════════════════════════
#  MODULE 1 · CAMELS RATING ENGINE
#  Capital · Asset Quality · Management · Earnings · Liquidity · Sensitivity
# ══════════════════════════════════════════════════════════════════
def analyze_camels(entity_data):
    a = entity_data.get("analysis", {})
    name = a.get("entity_name", a.get("bank_name", "Unknown"))

    prompt = f"""Perform a rigorous CAMELS supervisory rating for financial institution: {name}

Available data:
{json.dumps(a, ensure_ascii=False)[:2800]}

Apply FFIEC / Basel III supervisory standards. Return ONLY this JSON structure (no text outside):
{{
  "entity": "{name}",
  "camels_composite": {{
    "rating": 2,
    "label": "Satisfactory",
    "outlook": "Stable",
    "summary": "2-sentence executive assessment of overall financial health"
  }},
  "components": {{
    "capital_adequacy": {{
      "rating": 2,
      "tier1_ratio_est": 0.138,
      "car_estimate": 0.152,
      "leverage_ratio_est": 0.065,
      "basel_compliance": "Basel III compliant",
      "assessment": "Capital adequacy assessment based on available data",
      "risks": ["Capital concentration risk", "RWA inflation"]
    }},
    "asset_quality": {{
      "rating": 2,
      "npl_ratio_est": 0.018,
      "loan_loss_coverage_est": 1.4,
      "credit_concentration": "moderate",
      "ifrs9_stage_distribution": {{"stage1_pct": 0.82, "stage2_pct": 0.14, "stage3_pct": 0.04}},
      "assessment": "Asset quality assessment",
      "risks": ["Sector concentration"]
    }},
    "management_quality": {{
      "rating": 2,
      "governance_score": 7.2,
      "risk_culture": "strong",
      "strategic_execution": "on-track",
      "compliance_posture": "proactive",
      "assessment": "Management effectiveness assessment"
    }},
    "earnings": {{
      "rating": 2,
      "roe_est": 0.148,
      "roa_est": 0.012,
      "nim_est": 0.035,
      "cost_to_income_est": 0.48,
      "earnings_quality": "recurring",
      "assessment": "Earnings quality and sustainability assessment",
      "peer_comparison": "above median"
    }},
    "liquidity": {{
      "rating": 2,
      "lcr_est": 1.35,
      "nsfr_est": 1.12,
      "loan_to_deposit_est": 0.78,
      "liquidity_buffer_quality": "high-quality HQLA",
      "funding_diversification": "well-diversified",
      "assessment": "Liquidity position and funding structure assessment"
    }},
    "sensitivity_to_market_risk": {{
      "rating": 2,
      "interest_rate_sensitivity": "moderate",
      "duration_gap_est": 1.8,
      "fx_exposure": "limited",
      "equity_risk": "minimal",
      "assessment": "Market risk sensitivity assessment",
      "hedging_effectiveness": "adequate"
    }}
  }},
  "regulatory_flags": [],
  "peer_benchmarks": {{
    "regional_peer_group": "Southeast Asian commercial banks",
    "relative_position": "upper quartile",
    "key_differentiators": ["Strong digital capabilities", "Diversified income"]
  }},
  "supervisory_concerns": [],
  "positive_highlights": ["Adequate capital buffers", "Strong digital franchise", "Stable funding base"],
  "rating_trajectory": "improving"
}}"""

    try:
        raw = call_ai_api(prompt, max_tokens=2200)
        result = clean_json(raw)
        if result:
            result["_module"] = "camels"
            result["_generated_at"] = datetime.utcnow().isoformat()
        return result or _camels_fallback(name, "parse_error")
    except Exception as e:
        return _camels_fallback(name, str(e))


def _camels_fallback(name, err):
    return {
        "entity": name,
        "camels_composite": {"rating": 3, "label": "Fair", "outlook": "Stable",
                             "summary": f"Automated assessment limited. Error: {str(err)[:60]}"},
        "components": {k: {"rating": 3, "assessment": "Insufficient data"}
                       for k in ["capital_adequacy","asset_quality","management_quality",
                                 "earnings","liquidity","sensitivity_to_market_risk"]},
        "_module": "camels", "_error": str(err)
    }


# ══════════════════════════════════════════════════════════════════
#  MODULE 2 · DEEP RISK SCORING (LSTM+Transformer ensemble simulation)
#  Credit · Market · Liquidity · Operational · Systemic
# ══════════════════════════════════════════════════════════════════
def compute_deep_risk_score(entity_data):
    a = entity_data.get("analysis", {})
    name = a.get("entity_name", a.get("bank_name", "Unknown"))
    products = a.get("products", [])
    digital  = a.get("digital_capabilities", [])

    prompt = f"""You simulate an LSTM-Transformer ensemble risk model (Basel IRB calibrated, trained on 15Y global banking data).

Analyze counterparty/systemic risk for: {name}
Product lines: {len(products)} | Digital features: {len(digital)}
Competitive profile: {json.dumps(a.get("competitive_assessment", {}), ensure_ascii=False)[:600]}
Strategic positioning: {json.dumps(a.get("strategic_analysis", {}), ensure_ascii=False)[:400]}

Return ONLY this JSON (no text outside):
{{
  "entity": "{name}",
  "model_meta": {{
    "architecture": "BiLSTM-Transformer Ensemble v3.2",
    "training_data": "15Y global banking panel",
    "confidence_level": 0.95,
    "last_calibration": "Q1 2025"
  }},
  "credit_risk": {{
    "probability_of_default_1y": 0.0024,
    "probability_of_default_3y": 0.0089,
    "loss_given_default": 0.42,
    "exposure_at_default_multiplier": 1.08,
    "internal_credit_rating": "A-",
    "sp_equivalent": "BBB+",
    "moody_equivalent": "Baa1",
    "credit_watch": "stable",
    "rating_rationale": "1-sentence rationale"
  }},
  "systemic_risk": {{
    "d_sib_score": 0.34,
    "interconnectedness_index": 0.28,
    "contagion_risk": "low",
    "too_big_to_fail_probability": 0.12,
    "bail_in_buffer_adequacy": "adequate"
  }},
  "operational_risk": {{
    "composite_score": 6.2,
    "cyber_resilience_rating": "strong",
    "model_risk_exposure": "moderate",
    "conduct_risk_flags": 0,
    "aml_compliance_posture": "proactive"
  }},
  "market_risk": {{
    "var_99_1d_bps_of_equity": 145,
    "cvar_99_1d_bps_of_equity": 210,
    "stressed_var_multiplier": 3.1,
    "interest_rate_shock_100bps_pnl_impact_pct": -0.034,
    "fx_var_contribution_pct": 0.08
  }},
  "liquidity_risk": {{
    "intraday_liquidity_score": 8.1,
    "fire_sale_haircut_est": 0.08,
    "run_risk_30d": "low",
    "funding_concentration_hhi": 0.18,
    "contingent_funding_capacity_est": "adequate"
  }},
  "composite_risk_score": {{
    "overall": 72,
    "percentile_vs_regional_peers": 78,
    "trend_3m": "improving",
    "trend_12m": "stable",
    "rating_label": "Investment Grade · Low-Medium Risk",
    "color_code": "green"
  }},
  "stress_test_preview": {{
    "adverse_cet1_impact_bps": -145,
    "severely_adverse_cet1_impact_bps": -310,
    "passes_dfast_threshold": true,
    "passes_eba_threshold": true
  }},
  "lstm_feature_importance": [
    {{"feature": "NIM trend 12M",              "importance": 0.18, "direction": "negative"}},
    {{"feature": "NPL ratio change",            "importance": 0.15, "direction": "negative"}},
    {{"feature": "Digital revenue share",       "importance": 0.12, "direction": "positive"}},
    {{"feature": "Funding cost spread",         "importance": 0.11, "direction": "negative"}},
    {{"feature": "CET1 buffer above minimum",   "importance": 0.10, "direction": "positive"}},
    {{"feature": "Fee income diversification",  "importance": 0.09, "direction": "positive"}},
    {{"feature": "Loan-to-deposit ratio trend", "importance": 0.08, "direction": "mixed"}}
  ]
}}"""

    try:
        raw = call_ai_api(prompt, max_tokens=2000)
        result = clean_json(raw)
        if result:
            result["_module"] = "deep_risk"
        return result or {"entity": name, "_module": "deep_risk", "_error": "parse_failed",
                          "composite_risk_score": {"overall": 50, "rating_label": "Analysis Pending"}}
    except Exception as e:
        return {"entity": name, "_module": "deep_risk",
                "composite_risk_score": {"overall": 50, "rating_label": "API Error"},
                "_error": str(e)}


# ══════════════════════════════════════════════════════════════════
#  MODULE 3 · STRESS TESTING (Fed DFAST 2024 + EBA 2023 + BIS)
# ══════════════════════════════════════════════════════════════════
def run_stress_tests(entity_data):
    a    = entity_data.get("analysis", {})
    name = a.get("entity_name", a.get("bank_name", "Unknown"))

    prompt = f"""Apply Fed DFAST 2024, EBA 2023, and BIS stress testing to: {name}

Entity profile:
{json.dumps({k: a.get(k) for k in ["strategic_analysis","competitive_assessment","pricing"] if a.get(k)}, ensure_ascii=False)[:2000]}

Return ONLY this JSON with 5 stress scenarios:
{{
  "entity": "{name}",
  "methodology": "Fed DFAST 2024 + EBA 2023 + BIS Principles for Stress Testing",
  "base_capital": {{
    "starting_cet1": 0.148,
    "minimum_regulatory": 0.045,
    "combined_buffer_requirement": 0.025,
    "management_buffer": 0.02,
    "management_action_trigger": 0.10
  }},
  "scenarios": [
    {{
      "id": "base",
      "name": "Base Scenario",
      "description": "Moderate growth, stable rates, contained credit losses",
      "macro_assumptions": {{
        "gdp_growth": 0.025, "unemployment_rate": 0.062,
        "rate_change_bps": 0, "equity_market_change_pct": 0.08
      }},
      "impact": {{
        "cet1_ratio_end": 0.151, "npl_ratio_end": 0.021,
        "roe_end": 0.147, "net_income_change_pct": 0.06,
        "loan_loss_provisions_increase_pct": 0.12
      }},
      "passes_minimum": true,
      "narrative": "Bank maintains strong capital under benign conditions. NIM stable."
    }},
    {{
      "id": "adverse",
      "name": "Adverse Scenario",
      "description": "Moderate recession, +200bps rate spike, credit deterioration",
      "macro_assumptions": {{
        "gdp_growth": -0.015, "unemployment_rate": 0.092,
        "rate_change_bps": 200, "equity_market_change_pct": -0.28
      }},
      "impact": {{
        "cet1_ratio_end": 0.118, "npl_ratio_end": 0.048,
        "roe_end": 0.042, "net_income_change_pct": -0.45,
        "loan_loss_provisions_increase_pct": 1.8
      }},
      "passes_minimum": true,
      "narrative": "Capital drops 300bps but remains above regulatory minimum. Profitability pressured."
    }},
    {{
      "id": "severely_adverse",
      "name": "Severely Adverse Scenario",
      "description": "Deep recession, credit crunch, systemic financial stress",
      "macro_assumptions": {{
        "gdp_growth": -0.048, "unemployment_rate": 0.135,
        "rate_change_bps": -150, "equity_market_change_pct": -0.55
      }},
      "impact": {{
        "cet1_ratio_end": 0.086, "npl_ratio_end": 0.092,
        "roe_end": -0.068, "net_income_change_pct": -1.25,
        "loan_loss_provisions_increase_pct": 4.2
      }},
      "passes_minimum": true,
      "narrative": "Significant capital drawdown of 620bps, above 4.5% CET1 floor. Recovery path 24-36M."
    }},
    {{
      "id": "cyber_systemic",
      "name": "Cyber-Systemic Shock",
      "description": "Major cyber incident + reputational contagion + operational loss crystallization",
      "macro_assumptions": {{
        "gdp_growth": -0.012,
        "operational_loss_pct_of_revenue": 0.15,
        "deposit_outflow_pct": 0.08,
        "regulatory_fine_est_usd_m": 85
      }},
      "impact": {{
        "cet1_ratio_end": 0.102, "npl_ratio_end": 0.031,
        "roe_end": -0.012, "net_income_change_pct": -0.82,
        "operational_var_crystallized": true
      }},
      "passes_minimum": true,
      "narrative": "Cyber resilience investment limits impact. Full operational recovery within 18M."
    }},
    {{
      "id": "climate_transition",
      "name": "Climate Transition Risk (2030 horizon)",
      "description": "Aggressive carbon pricing, stranded assets in high-carbon sectors",
      "macro_assumptions": {{
        "carbon_price_usd_per_ton": 120,
        "high_carbon_loan_share_est": 0.14,
        "green_asset_premium_bps": 35,
        "physical_risk_provision_increase_pct": 0.22
      }},
      "impact": {{
        "cet1_ratio_end": 0.132, "npl_ratio_end": 0.028,
        "roe_end": 0.118, "net_income_change_pct": -0.18,
        "green_transition_opportunity_score": 7.4
      }},
      "passes_minimum": true,
      "narrative": "Moderate transition risk exposure. Early green finance positioning creates long-term value."
    }}
  ],
  "key_vulnerabilities": ["Concentration in rate-sensitive loan book", "Fee income dependence on transaction volumes"],
  "key_resilience_factors": ["Strong capital buffer", "Diversified funding base", "Digital revenue stream"],
  "overall_stress_verdict": "Resilient",
  "supervisory_recommendation": "No immediate action required. Monitor NPL trajectory in adverse scenario."
}}"""

    try:
        raw    = call_ai_api(prompt, max_tokens=3000)
        result = clean_json(raw)
        if result:
            result["_module"] = "stress_test"
        return result or {"entity": name, "_module": "stress_test",
                          "overall_stress_verdict": "Parse error", "_error": "JSON parse failed"}
    except Exception as e:
        return {"entity": name, "_module": "stress_test",
                "overall_stress_verdict": "API Error", "_error": str(e)}


# ══════════════════════════════════════════════════════════════════
#  MODULE 4 · LSTM 12-MONTH KPI FORECASTING
# ══════════════════════════════════════════════════════════════════
def generate_lstm_forecast(entity_data):
    a    = entity_data.get("analysis", {})
    name = a.get("entity_name", a.get("bank_name", "Unknown"))

    prompt = f"""You simulate a BiLSTM-3L + Attention neural network forecasting financial KPIs.

Generate 12-month forward projections for: {name}
Profile: {json.dumps(a.get("competitive_assessment", {}), ensure_ascii=False)[:500]}

Return ONLY JSON (generate realistic values with natural micro-variation):
{{
  "entity": "{name}",
  "model": {{
    "architecture": "BiLSTM-3L + Attention (hidden=256, seq_len=60)",
    "rmse_backtest": 0.0042, "mape_backtest": 0.038, "r2_score": 0.891
  }},
  "monthly_forecasts": [
    {{
      "month": 1, "label": "M+1",
      "nim": 0.0352, "nim_lower": 0.0331, "nim_upper": 0.0373,
      "roe": 0.148, "roe_lower": 0.131, "roe_upper": 0.165,
      "npl_ratio": 0.021, "npl_lower": 0.018, "npl_upper": 0.025,
      "car": 0.151, "deposit_growth": 0.028, "loan_growth": 0.031
    }}
  ],
  "trend_signals": {{
    "nim_trend": "compressing",
    "asset_quality_trend": "stable",
    "capital_trend": "building",
    "profitability_trend": "improving",
    "digital_revenue_trend": "accelerating"
  }},
  "key_inflection_points": [
    {{"month": 4, "event": "Rate cycle peak expected", "impact": "NIM compression reversal"}},
    {{"month": 8, "event": "Digital platform scale achieved", "impact": "Cost efficiency step-down"}}
  ],
  "summary_12m": {{
    "nim_end": 0.034, "roe_end": 0.152, "npl_end": 0.022,
    "car_end": 0.155, "deposit_growth_cumulative": 0.12,
    "loan_growth_cumulative": 0.14, "revenue_cagr_est": 0.089
  }}
}}
Include ALL 12 monthly entries with realistic values and confidence bands."""

    try:
        raw    = call_ai_api(prompt, max_tokens=3500)
        result = clean_json(raw)
        if result:
            result["_module"] = "lstm_forecast"
            if not result.get("monthly_forecasts"):
                result["monthly_forecasts"] = _synthetic_forecast()
        return result or {"entity": name, "_module": "lstm_forecast",
                          "monthly_forecasts": _synthetic_forecast(), "_note": "Synthetic fallback"}
    except Exception as e:
        return {"entity": name, "_module": "lstm_forecast",
                "monthly_forecasts": _synthetic_forecast(),
                "_note": "Synthetic fallback", "_error": str(e)}


def _synthetic_forecast():
    nim = 0.0355; roe = 0.142; npl = 0.022; car = 0.148
    rows = []
    for i in range(1, 13):
        nim += random.gauss(-0.0001, 0.0003)
        roe += random.gauss(0.001,   0.004)
        npl += random.gauss(0.0001,  0.0003)
        car += random.gauss(0.001,   0.002)
        rows.append({
            "month": i, "label": f"M+{i}",
            "nim":      round(nim, 4), "nim_lower": round(nim-.002, 4), "nim_upper": round(nim+.002, 4),
            "roe":      round(roe, 4), "roe_lower": round(roe-.015, 4), "roe_upper": round(roe+.015, 4),
            "npl_ratio":round(npl, 4), "npl_lower": round(npl-.002, 4), "npl_upper": round(npl+.003, 4),
            "car":      round(car, 4),
            "deposit_growth": round(random.uniform(.005, .025), 4),
            "loan_growth":    round(random.uniform(.008, .028), 4),
        })
    return rows


# ══════════════════════════════════════════════════════════════════
#  MODULE 5 · ESG SCORING (MSCI / Sustainalytics / TCFD)
# ══════════════════════════════════════════════════════════════════
def score_esg(entity_data):
    a    = entity_data.get("analysis", {})
    name = a.get("entity_name", a.get("bank_name", "Unknown"))

    prompt = f"""Apply MSCI ESG Rating + Sustainalytics + TCFD framework to: {name}

Profile: {json.dumps(a.get("strategic_analysis", {}), ensure_ascii=False)[:500]}
Products: {[p.get("name","") if isinstance(p,dict) else p for p in a.get("products", [])[:10]]}

Return ONLY JSON:
{{
  "entity": "{name}",
  "esg_composite": {{
    "score": 68,
    "rating": "BBB",
    "msci_equivalent": "BBB",
    "sustainalytics_risk_score": 22.4,
    "sustainalytics_risk_category": "Medium",
    "percentile_vs_peers": 64
  }},
  "environmental": {{
    "score": 62,
    "carbon_footprint_intensity": "moderate",
    "green_finance_commitment": "strong",
    "climate_risk_management": "improving",
    "green_loan_share_est": 0.18,
    "sustainable_bond_issuance": true,
    "tcfd_alignment": "partial",
    "key_initiatives": ["Green bond framework established", "Net-zero 2050 commitment"]
  }},
  "social": {{
    "score": 71,
    "financial_inclusion_score": 7.2,
    "gender_diversity_board_pct": 0.38,
    "community_investment_rating": "strong",
    "customer_data_privacy": "adequate",
    "employee_wellbeing_score": 7.4,
    "key_initiatives": ["SME lending expansion", "Digital literacy program"]
  }},
  "governance": {{
    "score": 74,
    "board_independence_pct": 0.72,
    "remuneration_transparency": "high",
    "audit_quality": "Big 4",
    "anti_corruption_program": "robust",
    "related_party_exposure": "low",
    "regulatory_enforcement_history": "clean",
    "key_initiatives": ["ESG board committee formed", "TCFD disclosure adopted"]
  }},
  "esg_risk_factors": ["Climate transition exposure in corporate loan book", "Cybersecurity governance gaps"],
  "esg_opportunities": ["Green mortgage product launch", "ESG-linked deposits", "Sustainability advisory services"],
  "regulatory_compliance": {{
    "eu_taxonomy_alignment": "partial",
    "sfdr_classification": "Article 8",
    "sbti_commitment": false,
    "un_pri_signatory": true
  }},
  "peer_esg_ranking": "above average",
  "improvement_roadmap": ["Adopt full TCFD reporting", "Launch SME green loan product", "Set SBTi targets by 2026"]
}}"""

    try:
        raw    = call_ai_api(prompt, max_tokens=2000)
        result = clean_json(raw)
        if result:
            result["_module"] = "esg"
        return result or {"entity": name, "_module": "esg",
                          "esg_composite": {"score": 55, "rating": "BB"}}
    except Exception as e:
        return {"entity": name, "_module": "esg",
                "esg_composite": {"score": 55, "rating": "BB"}, "_error": str(e)}


# ══════════════════════════════════════════════════════════════════
#  MODULE 6 · COMPETITIVE STRATEGY (McKinsey/BCG level)
# ══════════════════════════════════════════════════════════════════
def analyze_strategy(results):
    if not results:
        return {"executive_summary": "Không có dữ liệu để phân tích.",
                "competitive_ranking": [],
                "strategic_recommendations": {"overall_strategy": "N/A"}}

    summary = []
    for r in results:
        a = r.get("analysis", {})
        strategic   = a.get("strategic_analysis",   {})
        competitive = a.get("competitive_assessment",{})
        products    = a.get("products", [])
        prod_by_cat = {}
        for p in products:
            if isinstance(p, dict):
                prod_by_cat.setdefault(p.get("category","OTHER"), []).append(p.get("name",""))
        summary.append({
            "entity":   a.get("entity_name", a.get("bank_name", "Unknown")),
            "code":     a.get("entity_code",  a.get("bank_code", "")),
            "type":     r.get("entity_type",   a.get("entity_type", "bank")),
            "product_count":     len(products),
            "product_categories": list(prod_by_cat.keys()),
            "sample_products":   [f"{c}:{n}" for c,ns in prod_by_cat.items() for n in ns][:12],
            "digital_count":     len(a.get("digital_capabilities", [])),
            "digital_features":  a.get("digital_capabilities", [])[:6],
            "positioning":       strategic.get("positioning","")[:100],
            "value_proposition": strategic.get("value_proposition","")[:80],
            "target_segments":   strategic.get("target_segments",[])[:4],
            "key_differentiators":strategic.get("key_differentiators",[])[:4],
            "strengths":         competitive.get("strengths",[])[:4],
            "weaknesses":        competitive.get("weaknesses",[])[:3],
            "unique_selling_points":competitive.get("unique_selling_points",[])[:3],
            "market_position":   competitive.get("market_position",""),
            "threat_level":      competitive.get("competitive_threat_level",""),
            "data_confidence":   a.get("data_confidence","medium"),
            "source":            r.get("source","unknown"),
        })

    prompt = f"""You are a McKinsey Senior Partner, Global Banking Practice, 25 years experience.
Board-level competitive intelligence for {len(summary)} financial institutions:

{json.dumps(summary, ensure_ascii=False, indent=2)}

Return ONLY a comprehensive JSON competitive analysis:
{{
  "executive_summary": "4-5 sentence board synthesis: who leads, key dynamics, strategic imperatives. Reference specific entity names.",

  "market_overview": {{
    "total_entities_analyzed": {len(summary)},
    "market_maturity": "growing",
    "digital_disruption_stage": "mid",
    "consolidation_probability_3y": 0.35,
    "market_dynamics": "2-sentence specific market dynamics",
    "key_trends": ["Specific trend with evidence 1", "Trend 2", "Trend 3"],
    "disruption_factors": ["Factor 1", "Factor 2"],
    "total_addressable_market_est": "USD 45B by 2027"
  }},

  "competitive_ranking": [
    {{
      "rank": 1, "entity": "Name", "position": "Market position",
      "score": "8.5", "key_strength": "Core competitive advantage",
      "key_weakness": "Critical gap", "moat_type": "switching_costs",
      "analysis": "2-3 sentence specific competitive position analysis"
    }}
  ],

  "detailed_competitor_analysis": [
    {{
      "entity": "Name", "entity_type": "bank",
      "product_strategy": "Specific product strategy",
      "pricing_strategy": "Specific pricing approach",
      "distribution_strategy": "Channel strategy",
      "digital_strategy": "Digital maturity assessment",
      "target_customer": "Customer segment",
      "competitive_score": {{
        "product_breadth": 7, "digital_capability": 8,
        "pricing_competitiveness": 7, "brand_strength": 8,
        "customer_experience": 7, "innovation": 6,
        "risk_management": 7, "overall": 7
      }},
      "strategic_verdict": "1-2 sentence specific verdict"
    }}
  ],

  "product_comparison_matrix": {{
    "Core Banking": {{"leader":"Entity","ranking":["1st: Name","2nd: Name"],"gap_analysis":"Specific gap"}},
    "Digital & Mobile": {{"leader":"Entity","ranking":["1st: Name","2nd: Name"],"gap_analysis":"Digital gap"}},
    "Pricing & Rates": {{"leader":"Entity","ranking":["1st: Name","2nd: Name"],"gap_analysis":"Pricing analysis"}},
    "Customer Experience": {{"leader":"Entity","ranking":["1st: Name","2nd: Name"],"gap_analysis":"CX gap"}},
    "Risk Management": {{"leader":"Entity","ranking":["1st: Name","2nd: Name"],"gap_analysis":"Risk gap"}}
  }},

  "strategic_recommendations": {{
    "overall_strategy": "Specific strategy to achieve market leadership",
    "product_strategy": "Product portfolio moves: add, drop, invest",
    "pricing_strategy": "Pricing positioning recommendation",
    "distribution_strategy": "Channel optimization",
    "digital_strategy": "Digital transformation priorities",
    "quick_wins": ["0-3 month action 1", "Action 2", "Action 3"],
    "implementation_roadmap": [
      {{"phase":"Phase 1 (Q1-Q2 2025)","objective":"Specific objective","actions":["Action 1","Action 2","Action 3"],"milestones":"Measurable KPI","investment_required":"USD 15-25M"}},
      {{"phase":"Phase 2 (Q3-Q4 2025)","objective":"Scale","actions":["Action 1","Action 2"],"milestones":"KPI","investment_required":"USD 20-35M"}},
      {{"phase":"Phase 3 (2026)","objective":"Market leadership","actions":["Action 1","Action 2"],"milestones":"Long-term KPI","investment_required":"USD 40-60M"}}
    ]
  }},

  "market_opportunities": [
    {{"opportunity":"Specific opportunity","rationale":"Evidence-based rationale","potential_impact":"USD 500M+","difficulty":"Medium","priority":"High","time_to_capture":"12-18M","who_should_pursue":"Entity"}}
  ],

  "risk_mitigation": [
    {{"risk":"Specific risk","impact":"High","probability":"Medium","mitigation":"Specific mitigation","cost_of_inaction":"3-5% market share loss p.a."}}
  ],

  "competitive_intelligence_summary": {{
    "biggest_winner": "Entity and specific reasons",
    "biggest_threat": "Entity and threat mechanism",
    "hidden_gem": "Undervalued entity with potential",
    "key_battleground": "Specific product/segment where battle is fiercest",
    "inevitable_disruption": "What will change in 3-5 years"
  }},

  "m_and_a_landscape": {{
    "likely_acquirers": ["Entity 1"],
    "likely_targets": ["Entity 1"],
    "strategic_rationale": "Why M&A pressure exists",
    "probability_of_consolidation_3y": 0.4
  }}
}}"""

    try:
        content  = call_ai_api(prompt, max_tokens=4000, retries=4)
        strategy = clean_json(content)
        if not strategy:
            raise Exception("Cannot parse strategy JSON")
        return normalize_keys(strategy)
    except Exception as e:
        print(f"❌ Strategy analysis failed: {e}")
        return {
            "executive_summary": f"Strategy synthesis failed: {str(e)[:80]}. Entity analyses available.",
            "market_overview":   {"total_entities_analyzed": len(summary)},
            "competitive_ranking": [
                {"rank": i+1, "entity": s.get("entity",""), "score": "N/A",
                 "key_strength": ", ".join(s.get("strengths",[])[:1]),
                 "analysis": s.get("positioning","")}
                for i, s in enumerate(summary)
            ],
            "strategic_recommendations": {
                "overall_strategy": "Analysis failed — check GROQ_API_KEY_BK and retry."
            }
        }
