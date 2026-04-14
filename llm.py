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
        "messages": [{"role": "user", "content": prompt}],
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

def analyze_strategy(results):
    if not results:
        return {
            "executive_summary": "Không có dữ liệu đầu vào để phân tích chiến lược.",
            "competitive_ranking": [],
            "strategic_recommendations": {"overall_strategy": "N/A", "immediate_actions": []}
        }

    # Rút gọn dữ liệu để gửi cho AI (tránh quá tải tokens)
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

Trả về DUY NHẤT một JSON object theo đúng cấu trúc sau:
{{
  "executive_summary": "Tóm tắt...",
  "competitive_ranking": [
    {{"rank": 1, "bank": "...", "position": "...", "score": "...", "key_strength": "..."}}
  ],
  "strategic_recommendations": {{
    "overall_strategy": "...",
    "product_strategy": "...",
    "immediate_actions": ["..."]
  }}
}}"""

    try:
        content = call_groq_api(prompt, max_tokens=1400, retries=2)
        strategy = json.loads(content)
        return strategy
    except Exception as e:
        print(f"❌ Strategy parse error: {str(e)}")
        # Fallback khi AI lỗi hoặc parse JSON thất bại
        return {
            "executive_summary": "Có lỗi khi tổng hợp chiến lược bằng AI.",
            "competitive_ranking": [{"rank": 1, "bank": r.get("bank", "Bank"), "position": "N/A", "score": "N/A"} for r in summary],
            "strategic_recommendations": {
                "overall_strategy": "Vui lòng kiểm tra dữ liệu chi tiết của từng ngân hàng.",
                "product_strategy": "Cần xem xét thủ công.",
                "immediate_actions": ["Tải lại trang hoặc thử lại sau"]
            }
        }
