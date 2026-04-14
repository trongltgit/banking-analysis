import os
import traceback
import json
import time
import hashlib
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy


import pandas as pd
import PyPDF2
from io import BytesIO
from flask import request, jsonify

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

        # Giới hạn 3 URLs để tránh timeout
        if len(urls) > 3:
            urls = urls[:3]
            print(f"⚠️ Limited to 3 URLs to avoid timeout")

        # Check cache
        cache_key = get_cache_key(urls)
        if cache_key in _cache:
            print(f"♻️ Returning cached result for {cache_key[:8]}...")
            return jsonify({
                "status": "success",
                "results": _cache[cache_key]["results"],
                "strategy": _cache[cache_key]["strategy"],
                "cached": True,
                "meta": _cache[cache_key]["meta"]
            })

        results = []
        errors = []
        
        print(f"\n{'='*60}")
        print(f"🚀 DEEP AI ANALYSIS: {len(urls)} BANKS")
        print(f"{'='*60}\n")

        # Xử lý tuần tự với delay
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] 🔍 {url}")
            
            try:
                # Crawl
                raw = crawl_website(url)
                crawl_ok = not raw.startswith("ERROR_CRAWL")
                print(f"      {'✅' if crawl_ok else '⚠️'} Crawled {len(raw)} chars")
                
                # Delay trước AI
                time.sleep(1)
                
                # AI Extraction
                try:
                    extracted = extract_data(raw, url)
                    quality = extracted.get("extraction_quality", "unknown")
                    product_count = len(extracted.get("analysis", {}).get("products", []))
                    print(f"      ✅ AI Analysis: {quality} | {product_count} products")
                except Exception as e:
                    error_msg = str(e)
                    print(f"      ❌ AI Analysis failed: {error_msg[:60]}")
                    errors.append(f"{url}: {error_msg}")
                    
                    # Tạo result với lỗi nhưng không fail cả request
                    domain = url.split("//")[-1].split("/")[0].replace("www.", "").upper()
                    extracted = {
                        "url": url,
                        "analysis": {
                            "bank_name": f"{domain} (AI Error)",
                            "bank_code": None,
                            "products": [],
                            "strategic_analysis": {"positioning": f"AI failed: {error_msg[:40]}"},
                            "competitive_assessment": {"strengths": [], "weaknesses": [error_msg]}
                        },
                        "extraction_quality": "error"
                    }
                
                # Delay sau AI
                if idx < len(urls):  # Không delay sau cái cuối
                    time.sleep(2)
                
            except Exception as e:
                print(f"      ❌ Unexpected error: {str(e)[:60]}")
                errors.append(f"{url}: {str(e)}")
                continue

            results.append(safe_analysis(extracted))

        # Nếu tất cả đều lỗi
        if len(errors) == len(urls) and len(urls) > 0:
            return jsonify({
                "status": "error",
                "message": "Tất cả các ngân hàng đều phân tích thất bại",
                "errors": errors,
                "suggestion": "Có thể do rate limit Groq API. Đợi 1 phút và thử lại."
            }), 503

        print(f"\n{'='*60}")
        print("🧠 GENERATING STRATEGY...")
        print(f"{'='*60}\n")

        # Delay trước strategy
        time.sleep(1)
        
        # Strategy Generation
        try:
            strategy = analyze_strategy(results)
            print("      ✅ Strategy generated")
            
            if isinstance(strategy, str):
                strategy = json.loads(strategy)
                    
        except Exception as e:
            print(f"      ❌ Strategy failed: {str(e)[:60]}")
            # Strategy lỗi không fail cả request
            strategy = {
                "executive_summary": f"Strategy synthesis error: {str(e)[:60]}. Individual bank analyses are valid.",
                "competitive_ranking": [{"rank": i+1, "bank": r.get("bank_name", "Unknown"), "position": "Unknown", "score": "-"} for i, r in enumerate(results)],
                "strategic_recommendations": {
                    "overall_strategy": "Retry strategy generation",
                    "immediate_actions": ["Individual bank data is valid", "Retry for full strategy"]
                }
            }

        response_data = {
            "status": "success",
            "results": results,
            "strategy": strategy,
            "errors": errors if errors else None,
            "meta": {
                "banks_analyzed": len(results),
                "successful": len([r for r in results if r["extraction_quality"] != "error"]),
                "failed": len(errors),
                "total_products": sum(len(r["products"]) for r in results)
            }
        }
        
        # Cache kết quả
        _cache[cache_key] = response_data
        print(f"💾 Cached result for {cache_key[:8]}")

        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": str(e)


# ====================== PARSER MỚI ======================
def parse_uploaded_file(file_stream, filename):
    ext = filename.lower().split('.')[-1]
    data = []

    if ext in ['xlsx', 'xls']:
        df = pd.read_excel(file_stream)
    elif ext == 'csv':
        df = pd.read_csv(file_stream)
    elif ext == 'pdf':
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        # Dùng LLM parse PDF thành structured data
        prompt = f"""Trích xuất danh sách ngân hàng từ văn bản sau. Trả về JSON array:
        [{{"ten_ngan_hang": "...", "loai_san_pham": ["sản phẩm 1", "sản phẩm 2"]}}]
        Văn bản: {text[:15000]}"""
        try:
            raw = call_groq_api(prompt, max_tokens=1200)  # hàm bạn đã có trong llm.py
            data = json.loads(raw) if isinstance(raw, str) else raw
        except:
            return None, "Không parse được PDF"
        return data, None
    else:
        return None, "Định dạng file không hỗ trợ"

    # Chuẩn hóa cột cho XLSX/CSV
    col_map = {
        'ten_ngan_hang': ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank'],
        'loai_san_pham': ['loai_san_pham', 'san_pham', 'products', 'product_types']
    }
    df.columns = df.columns.str.strip().str.lower()

    for idx, row in df.iterrows():
        bank = None
        for possible in col_map['ten_ngan_hang']:
            if possible in df.columns:
                bank = str(row[possible]).strip()
                break
        products = []
        for possible in col_map['loai_san_pham']:
            if possible in df.columns:
                val = row[possible]
                if isinstance(val, str):
                    products = [x.strip() for x in val.split(',') if x.strip()]
                break
        if bank:
            data.append({"ten_ngan_hang": bank, "loai_san_pham": products})

    return data, None


# ====================== ROUTE MỚI ======================
@app.route('/api/analyze-upload', methods=['POST'])
def analyze_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "File rỗng"}), 400

    # Parse file
    file_stream = BytesIO(file.read())
    results, err = parse_uploaded_file(file_stream, file.filename)
    
    if err:
        return jsonify({"error": err}), 400
    if not results or len(results) == 0:
        return jsonify({"error": "KẾT QUẢ TRỐNG - File không có dữ liệu ngân hàng hợp lệ!"}), 400

    # Chuẩn bị dữ liệu cho analyze_strategy (dùng chung hàm bạn đã có)
    prepared = []
    for item in results:
        prepared.append({
            "analysis": {
                "bank_name": item["ten_ngan_hang"],
                "products": item["loai_san_pham"],
                "strategic_analysis": {"positioning": "Từ file upload"},
                "competitive_assessment": {"strengths": []}
            }
        })

    # Gọi strategy LLM
    strategy = analyze_strategy(prepared)

    return jsonify(strategy)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
