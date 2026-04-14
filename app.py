import os
import traceback
import json
import time
import hashlib
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy, call_groq_api # Đảm bảo call_groq_api có trong llm.py

import pandas as pd
import PyPDF2
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Simple cache
_cache = {}

def get_cache_key(urls):
    """Tạo cache key từ URLs"""
    return hashlib.md5(json.dumps(sorted(urls)).encode()).hexdigest()

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/health")
def health():
    return {"status": "ok", "version": "3.1-cached"}

def safe_analysis(item):
    """Normalize data"""
    a = item.get("analysis", {})
    return {
        "bank_name": a.get("bank_name") or "Unknown Bank",
        "bank_code": a.get("bank_code"),
        "products": a.get("products") or [],
        "interest_rates": a.get("interest_rates") or {},
        "promotions": a.get("promotions") or [],
        "digital_capabilities": a.get("digital_capabilities") or [],
        "strategic_analysis": a.get("strategic_analysis", {
            "positioning": "Unknown",
            "target_segments": [],
            "key_differentiators": [],
            "pricing_strategy": "Unknown",
            "distribution_strategy": "Unknown",
            "marketing_strategy": "Unknown"
        }),
        "competitive_assessment": a.get("competitive_assessment", {
            "strengths": [],
            "weaknesses": [],
            "market_position": "Unknown",
            "competitive_threat_level": "Unknown"
        }),
        "product_gaps_vs_market": a.get("product_gaps_vs_market", []),
        "url": item.get("url"),
        "extraction_quality": item.get("extraction_quality", "unknown")
    }

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls:
            return jsonify({"status": "error", "message": "No URLs provided"}), 400

        if len(urls) > 3:
            urls = urls[:3]
            print(f"⚠️ Limited to 3 URLs to avoid timeout")

        cache_key = get_cache_key(urls)
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        results = []
        errors = []
        
        for idx, url in enumerate(urls, 1):
            try:
                raw = crawl_website(url)
                time.sleep(1)
                extracted = extract_data(raw, url)
                results.append(safe_analysis(extracted))
                if idx < len(urls): time.sleep(2)
            except Exception as e:
                errors.append(f"{url}: {str(e)}")

        if len(errors) == len(urls) and len(urls) > 0:
            return jsonify({"status": "error", "errors": errors}), 503

        strategy = analyze_strategy(results)
        if isinstance(strategy, str):
            strategy = json.loads(strategy)

        response_data = {
            "status": "success",
            "results": results,
            "strategy": strategy,
            "meta": {"successful": len(results), "failed": len(errors)}
        }
        
        _cache[cache_key] = response_data
        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ====================== PARSER MỚI ======================
def parse_uploaded_file(file_stream, filename):
    ext = filename.lower().split('.')[-1]
    data = []

    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(file_stream)
        elif ext == 'csv':
            df = pd.read_csv(file_stream)
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(file_stream)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            prompt = f"Trích xuất danh sách ngân hàng từ văn bản sau. Trả về JSON array: [{{'ten_ngan_hang': '...', 'loai_san_pham': []}}]. Văn bản: {text[:10000]}"
            raw = call_groq_api(prompt)
            return (json.loads(raw) if isinstance(raw, str) else raw), None
        else:
            return None, "Định dạng file không hỗ trợ"

        col_map = {
            'ten_ngan_hang': ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank'],
            'loai_san_pham': ['loai_san_pham', 'san_pham', 'products']
        }
        df.columns = df.columns.str.strip().str.lower()

        for _, row in df.iterrows():
            bank = next((str(row[c]).strip() for c in col_map['ten_ngan_hang'] if c in df.columns), None)
            prods = next((row[c] for c in col_map['loai_san_pham'] if c in df.columns), "")
            if isinstance(prods, str):
                prods = [x.strip() for x in prods.split(',') if x.strip()]
            if bank:
                data.append({"ten_ngan_hang": bank, "loai_san_pham": prods})
        return data, None
    except Exception as e:
        return None, str(e)

@app.route('/api/analyze-upload', methods=['POST'])
def analyze_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400

    file = request.files['file']
    file_stream = BytesIO(file.read())
    results, err = parse_uploaded_file(file_stream, file.filename)
    
    if err: return jsonify({"error": err}), 400
    
    prepared = [{"analysis": {"bank_name": i["ten_ngan_hang"], "products": i["loai_san_pham"]}} for i in results]
    strategy = analyze_strategy(prepared)
    return jsonify(strategy)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
