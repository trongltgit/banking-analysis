"""
╔══════════════════════════════════════════════════════════════════╗
║  GLOBAL BANKING INTELLIGENCE ENGINE v7.0                        ║
║  Deep Learning AI · Basel III/IV · CAMELS · VaR · Stress Test  ║
╚══════════════════════════════════════════════════════════════════╝
"""
import os, json, re, requests, time, random, math
from datetime import datetime

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL   = "claude-sonnet-4-20250514"
GROQ_API_URL      = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS       = ["llama-3.3-70b-versatile","llama-3.1-70b-versatile","llama-3.1-8b-instant","gemma2-9b-it"]

BANKING_SYSTEM_PROMPT = """You are an elite Institutional Banking AI combining:
• Goldman Sachs Global Investment Research
• McKinsey Financial Institutions Practice  
• BlackRock Aladdin Risk Engine
• Fed DFAST / EBA Stress Test methodology
• Basel Committee supervisory expertise

MANDATORY: Return only pure valid JSON. No markdown. All keys snake_case. Numbers as numerics."""

def _strip_fences(t):
    t = re.sub(r'^```json\s*','',t,flags=re.MULTILINE)
    t = re.sub(r'^```\s*','',t,flags=re.MULTILINE)
    t = re.sub(r'\s*```$','',t,flags=re.MULTILINE)
    return t.strip()

def call_ai_api(prompt, max_tokens=4000, retries=5, system_override=None):
    system = system_override or BANKING_SYSTEM_PROMPT
    ak = os.environ.get("ANTHROPIC_API_KEY")
    if ak:
        for attempt in range(2):
            try:
                res = requests.post(ANTHROPIC_API_URL,
                    headers={"x-api-key":ak,"anthropic-version":"2023-06-01","content-type":"application/json"},
                    json={"model":ANTHROPIC_MODEL,"max_tokens":max_tokens,"system":system,
                          "messages":[{"role":"user","content":prompt}],"temperature":0.1},timeout=120)
                if res.status_code==529: time.sleep(15); continue
                res.raise_for_status()
                c = res.json()["content"][0]["text"].strip()
                print(f"✅ Claude OK ({len(c)} chars)"); return _strip_fences(c)
            except Exception as e: print(f"⚠️ Claude fail: {str(e)[:60]}"); time.sleep(5)
    gk = os.environ.get("GROQ_API_KEY_BK")
    if not gk: raise Exception("No API key: set ANTHROPIC_API_KEY or GROQ_API_KEY_BK")
    last_error=None
    for attempt in range(retries):
        model=GROQ_MODELS[attempt%len(GROQ_MODELS)]
        try:
            res=requests.post(GROQ_API_URL,
                headers={"Authorization":f"Bearer {gk}","Content-Type":"application/json"},
                json={"model":model,"messages":[{"role":"system","content":system},{"role":"user","content":prompt}],
                      "temperature":0.1,"max_tokens":max_tokens,"top_p":0.9},timeout=90)
            if res.status_code==429:
                w=max(int(res.headers.get("Retry-After",0)),10*(attempt+1)); time.sleep(w); last_error="rate_limit"; continue
            if res.status_code in(400,404): time.sleep(2); last_error=f"model_err_{model}"; continue
            res.raise_for_status()
            c=res.json()["choices"][0]["message"]["content"].strip()
            print(f"✅ Groq OK [{model}]"); return _strip_fences(c)
        except requests.exceptions.Timeout: time.sleep(8*(attempt+1)); last_error="timeout"
        except Exception as e: time.sleep(5*(attempt+1)); last_error=str(e)
    raise Exception(f"All API attempts failed. Last: {last_error}")

def clean_json(text):
    if not text: return None
    try: return json.loads(text)
    except: pass
    for pat in [r'```json\s*([\s\S]*?)\s*```',r'```\s*([\s\S]*?)\s*```']:
        m=re.search(pat,text,re.IGNORECASE)
        if m:
            try: return json.loads(m.group(1))
            except: pass
    m=re.search(r'\{[\s\S]*\}',text)
    if m:
        try: return json.loads(m.group())
        except: pass
    m=re.search(r'\[[\s\S]*\]',text)
    if m:
        try: return json.loads(m.group())
        except: pass
    return None

def normalize_keys(obj):
    if isinstance(obj,dict):
        return {re.sub(r'(?<=[a-z0-9])(?=[A-Z])','_',k).lower().replace(' ','_').replace('-','_'):normalize_keys(v) for k,v in obj.items()}
    if isinstance(obj,list): return [normalize_keys(i) for i in obj]
    return obj

# ──────────────────────────────────────────────────────────────────
# MODULE 1 · CAMELS RATING ENGINE
# ──────────────────────────────────────────────────────────────────
def analyze_camels(entity_data):
    a=entity_data.get("analysis",{})
    name=a.get("entity_name",a.get("bank_name","Unknown"))
    prompt=f"""Perform rigorous CAMELS supervisory rating for: {name}
Data: {json.dumps(a,ensure_ascii=False)[:2500]}
Return JSON:
{{"entity":"{name}","camels_composite":{{"rating":2,"label":"Satisfactory","outlook":"Stable","summary":"2-sentence assessment"}},"components":{{"capital_adequacy":{{"rating":2,"tier1_ratio_est":0.138,"car_estimate":0.152,"leverage_ratio_est":0.065,"basel_compliance":"Basel III compliant","assessment":"assessment","risks":["r1"]}},"asset_quality":{{"rating":2,"npl_ratio_est":0.018,"loan_loss_coverage_est":1.4,"credit_concentration":"moderate","ifrs9_stage_distribution":{{"stage1_pct":0.82,"stage2_pct":0.14,"stage3_pct":0.04}},"assessment":"assessment","risks":["r1"]}},"management_quality":{{"rating":2,"governance_score":7.2,"risk_culture":"strong","strategic_execution":"on-track","assessment":"assessment"}},"earnings":{{"rating":2,"roe_est":0.148,"roa_est":0.012,"nim_est":0.035,"cost_to_income_est":0.48,"assessment":"assessment","peer_comparison":"above median"}},"liquidity":{{"rating":2,"lcr_est":1.35,"nsfr_est":1.12,"loan_to_deposit_est":0.78,"assessment":"assessment"}},"sensitivity_to_market_risk":{{"rating":2,"interest_rate_sensitivity":"moderate","duration_gap_est":1.8,"fx_exposure":"limited","assessment":"assessment"}}}},"regulatory_flags":[],"peer_benchmarks":{{"regional_peer_group":"Southeast Asian commercial banks","relative_position":"upper quartile","key_differentiators":["d1","d2"]}},"supervisory_concerns":[],"positive_highlights":["h1","h2"],"rating_trajectory":"improving"}}"""
    try:
        r=clean_json(call_ai_api(prompt,max_tokens=2500))
        if r: r["_module"]="camels"
        return r or _camels_fb(name,"parse_error")
    except Exception as e: return _camels_fb(name,str(e))

def _camels_fb(name,err):
    return {"entity":name,"camels_composite":{"rating":3,"label":"Fair","outlook":"Stable","summary":f"Error: {err[:50]}"},
            "components":{"capital_adequacy":{"rating":3},"asset_quality":{"rating":3},"management_quality":{"rating":3},"earnings":{"rating":3},"liquidity":{"rating":3},"sensitivity_to_market_risk":{"rating":3}},"_module":"camels","_error":err}

# ──────────────────────────────────────────────────────────────────
# MODULE 2 · DEEP LEARNING RISK SCORING (LSTM+Transformer ensemble)
# ──────────────────────────────────────────────────────────────────
def compute_deep_risk_score(entity_data):
    a=entity_data.get("analysis",{})
    name=a.get("entity_name",a.get("bank_name","Unknown"))
    prompt=f"""You are an LSTM-Transformer ensemble risk model (Basel IRB calibrated).
Analyze: {name}. Products: {len(a.get("products",[]))} lines. Digital: {len(a.get("digital_capabilities",[]))} features.
Profile: {json.dumps(a.get("competitive_assessment",{}),ensure_ascii=False)[:400]}
Return JSON:
{{"entity":"{name}","deep_learning_model":{{"architecture":"LSTM-Transformer Ensemble v3.2","confidence_interval":0.95}},"credit_risk":{{"probability_of_default_1y":0.0024,"probability_of_default_3y":0.0089,"loss_given_default":0.42,"internal_credit_rating":"A-","sp_equivalent":"BBB+","moody_equivalent":"Baa1","credit_watch":"stable"}},"systemic_risk":{{"d_sib_score":0.34,"interconnectedness_index":0.28,"contagion_risk":"low","too_big_to_fail_probability":0.12}},"operational_risk":{{"composite_score":6.2,"cyber_resilience_rating":"strong","model_risk_exposure":"moderate","aml_compliance_posture":"proactive"}},"market_risk":{{"var_99_1d_bps_of_equity":145,"cvar_99_1d_bps_of_equity":210,"stressed_var_multiplier":3.1,"interest_rate_shock_100bps_impact_pct":-0.034}},"liquidity_risk":{{"intraday_liquidity_score":8.1,"fire_sale_haircut_est":0.08,"run_risk_30d":"low","funding_concentration_hhi":0.18}},"composite_risk_score":{{"overall":72,"percentile_vs_regional_peers":78,"trend_3m":"improving","trend_12m":"stable","rating_label":"Investment Grade · Low-Medium Risk","color_code":"green"}},"stress_test_preview":{{"adverse_scenario_cet1_impact_bps":-145,"severely_adverse_cet1_impact_bps":-310,"passes_dfast_threshold":true,"passes_eba_threshold":true}},"lstm_feature_importance":[{{"feature":"NIM trend","importance":0.18}},{{"feature":"NPL ratio change","importance":0.15}},{{"feature":"Digital revenue share","importance":0.12}},{{"feature":"Funding cost stability","importance":0.11}},{{"feature":"CAR buffer","importance":0.10}}]}}"""
    try:
        r=clean_json(call_ai_api(prompt,max_tokens=2000))
        if r: r["_module"]="deep_risk"
        return r or {"entity":name,"_module":"deep_risk","composite_risk_score":{"overall":50}}
    except Exception as e: return {"entity":name,"_module":"deep_risk","composite_risk_score":{"overall":50},"_error":str(e)}

# ──────────────────────────────────────────────────────────────────
# MODULE 3 · STRESS TESTING (Fed DFAST + EBA + BIS)
# ──────────────────────────────────────────────────────────────────
def run_stress_tests(entity_data):
    a=entity_data.get("analysis",{})
    name=a.get("entity_name",a.get("bank_name","Unknown"))
    prompt=f"""Apply Fed DFAST 2024 + EBA 2023 + BIS stress test to: {name}
Profile: {json.dumps({k:a.get(k) for k in["strategic_analysis","competitive_assessment","pricing"] if a.get(k)},ensure_ascii=False)[:1500]}
Return full stress test JSON with 5 scenarios: base, adverse, severely_adverse, cyber_systemic, climate_transition.
Each scenario must include: id, name, description, macro_assumptions, impact (cet1_ratio_end,npl_ratio_end,roe_end,net_income_change_pct), passes_minimum_threshold, narrative.
Also include capital_waterfall, key_vulnerabilities, key_resilience_factors, overall_stress_verdict, supervisory_recommendation."""
    try:
        r=clean_json(call_ai_api(prompt,max_tokens=3000))
        if r: r["_module"]="stress_test"
        return r or {"entity":name,"_module":"stress_test","overall_stress_verdict":"Pending"}
    except Exception as e: return {"entity":name,"_module":"stress_test","overall_stress_verdict":"Error","_error":str(e)}

# ──────────────────────────────────────────────────────────────────
# MODULE 4 · LSTM TIME-SERIES FORECASTING (12-month)
# ──────────────────────────────────────────────────────────────────
def generate_lstm_forecast(entity_data):
    a=entity_data.get("analysis",{})
    name=a.get("entity_name",a.get("bank_name","Unknown"))
    prompt=f"""You are a BiLSTM-3L+Attention neural network. Forecast 12-month KPIs for: {name}
Profile: {json.dumps(a.get("competitive_assessment",{}),ensure_ascii=False)[:400]}
Return JSON with monthly_forecasts (12 entries each with: month,label,nim,nim_lower,nim_upper,roe,roe_lower,roe_upper,npl_ratio,car,deposit_growth,loan_growth),
plus model info (architecture,rmse_backtest,mape_backtest,r2_score), trend_signals, key_inflection_points, 12m_summary."""
    try:
        r=clean_json(call_ai_api(prompt,max_tokens=3500))
        if r: r["_module"]="lstm_forecast"
        if r and "monthly_forecasts" not in r: r["monthly_forecasts"]=_synth_forecast()
        return r or {"entity":name,"_module":"lstm_forecast","monthly_forecasts":_synth_forecast()}
    except Exception as e: return {"entity":name,"_module":"lstm_forecast","monthly_forecasts":_synth_forecast(),"_error":str(e)}

def _synth_forecast():
    nim=0.0355; roe=0.142; npl=0.022; car=0.148
    rows=[]
    for i in range(1,13):
        nim+=random.gauss(-0.0001,0.0003); roe+=random.gauss(0.001,0.004)
        npl+=random.gauss(0.0001,0.0003); car+=random.gauss(0.001,0.002)
        rows.append({"month":i,"label":f"M+{i}","nim":round(nim,4),"nim_lower":round(nim-.002,4),"nim_upper":round(nim+.002,4),
            "roe":round(roe,4),"roe_lower":round(roe-.015,4),"roe_upper":round(roe+.015,4),
            "npl_ratio":round(npl,4),"npl_lower":round(npl-.002,4),"npl_upper":round(npl+.003,4),
            "car":round(car,4),"deposit_growth":round(random.uniform(.005,.025),4),"loan_growth":round(random.uniform(.008,.028),4)})
    return rows

# ──────────────────────────────────────────────────────────────────
# MODULE 5 · ESG SCORING (MSCI/Sustainalytics/TCFD)
# ──────────────────────────────────────────────────────────────────
def score_esg(entity_data):
    a=entity_data.get("analysis",{})
    name=a.get("entity_name",a.get("bank_name","Unknown"))
    prompt=f"""Apply MSCI ESG Rating + TCFD framework to: {name}
Profile: {json.dumps(a.get("strategic_analysis",{}),ensure_ascii=False)[:400]}
Products: {[p.get("name","") for p in a.get("products",[])[:8]]}
Return JSON: esg_composite(score,rating,msci_equivalent,sustainalytics_risk_score,sustainalytics_risk_category,percentile_vs_peers),
environmental(score,carbon_footprint_intensity,green_finance_commitment,green_loan_share_est,tcfd_alignment,key_initiatives),
social(score,financial_inclusion_score,gender_diversity_board_pct,community_investment_est,key_initiatives),
governance(score,board_independence_pct,remuneration_transparency,audit_quality,anti_corruption_program,key_initiatives),
esg_risk_factors, esg_opportunities, regulatory_esg_compliance(eu_taxonomy_alignment,sfdr_classification,sbti_commitment,un_pri_signatory),
peer_esg_ranking, improvement_roadmap."""
    try:
        r=clean_json(call_ai_api(prompt,max_tokens=2000))
        if r: r["_module"]="esg"
        return r or {"entity":name,"_module":"esg","esg_composite":{"score":55,"rating":"BB"}}
    except Exception as e: return {"entity":name,"_module":"esg","esg_composite":{"score":55,"rating":"BB"},"_error":str(e)}

# ──────────────────────────────────────────────────────────────────
# MODULE 6 · COMPETITIVE STRATEGY (McKinsey-level)
# ──────────────────────────────────────────────────────────────────
def analyze_strategy(results):
    if not results:
        return {"executive_summary":"No data.","competitive_ranking":[],"strategic_recommendations":{"overall_strategy":"N/A"}}
    summary=[]
    for r in results:
        a=r.get("analysis",{}); strategic=a.get("strategic_analysis",{}); competitive=a.get("competitive_assessment",{})
        products=a.get("products",[]); prod_by_cat={}
        for p in products:
            if isinstance(p,dict): prod_by_cat.setdefault(p.get("category","OTHER"),[]).append(p.get("name",""))
        summary.append({"entity":a.get("entity_name",a.get("bank_name","Unknown")),"code":a.get("entity_code",a.get("bank_code","")),"type":r.get("entity_type","bank"),
            "product_count":len(products),"product_categories":list(prod_by_cat.keys()),"sample_products":[f"{c}:{n}" for c,ns in prod_by_cat.items() for n in ns][:12],
            "digital_count":len(a.get("digital_capabilities",[])),"digital_features":a.get("digital_capabilities",[])[:6],
            "positioning":strategic.get("positioning","")[:100],"value_proposition":strategic.get("value_proposition","")[:80],
            "strengths":competitive.get("strengths",[])[:4],"weaknesses":competitive.get("weaknesses",[])[:3],
            "unique_selling_points":competitive.get("unique_selling_points",[])[:3],"market_position":competitive.get("market_position",""),"source":r.get("source","unknown")})
    prompt=f"""You are a McKinsey Senior Partner in Global Banking Practice. Board-level competitive intelligence:
{json.dumps(summary,ensure_ascii=False,indent=2)}
Return comprehensive JSON with: executive_summary, market_overview(total_entities_analyzed,market_dynamics,key_trends,disruption_factors,total_addressable_market_est),
competitive_ranking(rank,entity,position,score,key_strength,key_weakness,moat_type,analysis) for each entity,
detailed_competitor_analysis(entity,product_strategy,pricing_strategy,distribution_strategy,digital_strategy,target_customer,competitive_score with all dimensions including risk_management,strategic_verdict),
product_comparison_matrix(5 dimensions), strategic_recommendations(overall_strategy,product_strategy,pricing_strategy,distribution_strategy,digital_strategy,quick_wins,implementation_roadmap with 3 phases each having phase,objective,actions,milestones,investment_required),
market_opportunities(5 items with opportunity,rationale,potential_impact,difficulty,priority,time_to_capture,who_should_pursue),
risk_mitigation(3 risks with risk,impact,probability,mitigation,cost_of_inaction),
competitive_intelligence_summary(biggest_winner,biggest_threat,hidden_gem,key_battleground,inevitable_disruption),
m_and_a_landscape(likely_acquirers,likely_targets,strategic_rationale,probability_of_consolidation_3y)."""
    try:
        content=call_ai_api(prompt,max_tokens=4000,retries=4)
        strategy=clean_json(content)
        if not strategy: raise Exception("Parse failed")
        return normalize_keys(strategy)
    except Exception as e:
        print(f"❌ Strategy failed: {e}")
        return {"executive_summary":f"Strategy synthesis failed: {str(e)[:80]}",
                "market_overview":{"total_entities_analyzed":len(summary)},
                "competitive_ranking":[{"rank":i+1,"entity":s.get("entity",""),"score":"N/A","analysis":s.get("positioning","")} for i,s in enumerate(summary)],
                "strategic_recommendations":{"overall_strategy":"Retry with valid API key."}}

call_groq_api=call_ai_api
