


import os
import traceback
import json
import time
import hashlib
import csv
import io
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy, call_groq_api
import PyPDF2

app = Flask(__name__)
CORS(app)

_cache = {}

def get_cache_key(urls):
    return hashlib.md5(json.dumps(sorted(urls)).encode()).hexdigest()

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/health")
def health():
    return {"status": "ok", "version": "4.0-enhanced"}

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls:
            return jsonify({"status": "error", "message": "No URLs provided"}), 400

        if len(urls) > 4:
            urls = urls[:4]

        cache_key = get_cache_key(urls)
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        results = []
        errors = []
        
        for idx, url in enumerate(urls, 1):
            try:
                print(f"🔍 Crawling {url}...")
                raw = crawl_website(url)
                
                if not raw or raw.startswith("ERROR_CRAWL"):
                    raise Exception(f"Cannot crawl website")
                
                print(f"📄 Extracted {len(raw)} chars")
                time.sleep(1)
                
                extracted = extract_data(raw, url)
                results.append(extracted)
                
                if idx < len(urls): 
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                errors.append(f"{url}: {str(e)}")

        if len(results) == 0:
            return jsonify({
                "status": "error", 
                "message": "All URLs failed to crawl",
                "errors": errors
            }), 503

        print(f"✅ Crawled {len(results)} URLs, analyzing strategy...")
        strategy = analyze_strategy(results)
        
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

def parse_uploaded_file(file_stream, filename):
    ext = filename.lower().split('.')[-1]
    data = []

    try:
        if ext in ['xlsx', 'xls']:
            from openpyxl import load_workbook
            wb = load_workbook(file_stream)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            
            if len(rows) < 2:
                return None, "File không đủ dữ liệu"
            
            # Tìm header
            header_idx = None
            for i, row in enumerate(rows):
                if row and row[0]:
                    if str(row[0]).strip().lower() in ['ten_ngan_hang', 'ngân hàng', 'bank']:
                        header_idx = i
                        break
            
            if header_idx is None:
                return None, "Không tìm thấy cột 'ten_ngan_hang'"
            
            # Đọc data
            for i in range(header_idx + 1, len(rows)):
                row = rows[i]
                if not row or not row[0]:
                    continue
                
                bank_name = str(row[0]).strip()
                all_products = []
                
                for col_idx in range(1, len(row)):
                    if row[col_idx]:
                        prod_text = str(row[col_idx]).strip()
                        products = [p.strip() for p in re.split(r'[;,]', prod_text) if p.strip()]
                        all_products.extend(products)
                
                if all_products:
                    data.append({
                        "ten_ngan_hang": bank_name,
                        "loai_san_pham": all_products
                    })
                    
        elif ext == 'csv':
            content = file_stream.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                bank = None
                prods = []
                
                for key in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank']:
                    if key in row and row[key]:
                        bank = row[key].strip()
                        break
                
                for key, val in row.items():
                    if key not in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank'] and val:
                        products = [p.strip() for p in re.split(r'[;,]', str(val)) if p.strip()]
                        prods.extend(products)
                
                if bank and prods:
                    data.append({"ten_ngan_hang": bank, "loai_san_pham": prods})
                    
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(file_stream)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            prompt = f"Trích xuất danh sách ngân hàng và sản phẩm. Trả về JSON array: [{{'ten_ngan_hang': '...', 'loai_san_pham': ['sp1', 'sp2']}}]. Văn bản: {text[:5000]}"
            raw = call_groq_api(prompt)
            try:
                return json.loads(raw), None
            except:
                return None, "Không thể parse PDF"
        else:
            return None, "Định dạng không hỗ trợ"

        return data if data else None, None
        
    except Exception as e:
        return None, f"Lỗi parse: {str(e)}"

@app.route('/api/analyze-upload', methods=['POST'])
def analyze_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "File rỗng"}), 400
        
    file_stream = io.BytesIO(file.read())
    results, err = parse_uploaded_file(file_stream, file.filename)
    
    if err:
        return jsonify({"error": err}), 400
    
    if not results:
        return jsonify({"error": "Không parse được dữ liệu"}), 400
    
    prepared = []
    for item in results:
        prepared.append({
            "analysis": {
                "bank_name": item["ten_ngan_hang"],
                "products": [{"name": p, "category": "UNKNOWN"} for p in item["loai_san_pham"]],
                "promotions": [],
                "digital_capabilities": [],
                "strategic_analysis": {},
                "competitive_assessment": {}
            }
        })
    
    strategy = analyze_strategy(prepared)
            
    return jsonify({
        "status": "success",
        "results": results,
        "strategy": strategy
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
