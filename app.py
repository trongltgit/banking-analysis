import os
import traceback
import json
import time
import hashlib
import csv
import io
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy, call_groq_api
import PyPDF2

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
    return {"status": "ok", "version": "3.5-real-analysis"}

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls:
            return jsonify({"status": "error", "message": "No URLs provided"}), 400

        if len(urls) > 4:
            urls = urls[:4]
            print(f"⚠️ Limited to 4 URLs to avoid timeout")

        cache_key = get_cache_key(urls)
        if cache_key in _cache:
            return jsonify(_cache[cache_key])

        results = []
        errors = []
        
        for idx, url in enumerate(urls, 1):
            try:
                print(f"🔍 Crawling {url}...")
                raw = crawl_website(url)
                
                # Kiểm tra lỗi crawl
                if raw.startswith("ERROR_CRAWL"):
                    raise Exception(f"Cannot crawl website: {raw}")
                
                print(f"📄 Extracted {len(raw)} chars from {url}")
                time.sleep(1)
                
                extracted = extract_data(raw, url)
                results.append(extracted)
                
                if idx < len(urls): 
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                errors.append(f"{url}: {str(e)}")

        if len(errors) == len(urls) and len(urls) > 0:
            return jsonify({
                "status": "error", 
                "message": "All URLs failed to crawl",
                "errors": errors
            }), 503

        print(f"✅ Successfully crawled {len(results)} URLs, analyzing strategy...")
        strategy = analyze_strategy(results)
        
        response_data = {
            "status": "success",
            "results": results,
            "strategy": strategy,
            "meta": {"successful": len(results), "failed": len(errors), "errors": errors}
        }
        
        _cache[cache_key] = response_data
        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ====================== FILE UPLOAD - HỖ TRỢ EXCEL NHIỀU CỘT ======================
def parse_uploaded_file(file_stream, filename):
    ext = filename.lower().split('.')[-1]
    data = []

    try:
        if ext in ['xlsx', 'xls']:
            from openpyxl import load_workbook
            wb = load_workbook(file_stream)
            ws = wb.active
            
            # Đọc tất cả rows
            rows = list(ws.iter_rows(values_only=True))
            if len(rows) < 2:
                return None, "File không có dữ liệu"
            
            # Tìm header row (row chứa "ten_ngan_hang")
            header_row_idx = None
            for i, row in enumerate(rows):
                if row and len(row) > 0 and row[0] and 'ten_ngan_hang' in str(row[0]).lower():
                    header_row_idx = i
                    break
            
            if header_row_idx is None:
                # Thử tìm row đầu tiên có dữ liệu
                for i, row in enumerate(rows):
                    if row and len(row) > 0 and row[0] and str(row[0]).strip():
                        header_row_idx = i
                        break
            
            if header_row_idx is None:
                return None, "Không tìm thấy header trong file Excel"
            
            headers = [str(h).lower().strip() if h else '' for h in rows[header_row_idx]]
            print(f"📊 Headers found: {headers}")
            
            # Tìm cột tên ngân hàng (cột đầu tiên)
            bank_col = 0
            
            # Các cột còn lại là loại sản phẩm
            product_cols = []
            for i, h in enumerate(headers[1:], 1):
                if h and h != 'loai_san_pham':
                    product_cols.append((i, h))
            
            print(f"🏦 Bank col: {bank_col}, Product cols: {[h for _, h in product_cols]}")
            
            # Đọc data từ các row sau header
            for row in rows[header_row_idx + 1:]:
                if len(row) > bank_col and row[bank_col]:
                    bank_name = str(row[bank_col]).strip()
                    if not bank_name or bank_name.lower() == 'ten_ngan_hang':
                        continue
                    
                    # Thu thập tất cả sản phẩm từ các cột
                    all_products = []
                    for col_idx, col_name in product_cols:
                        if len(row) > col_idx and row[col_idx]:
                            prod_text = str(row[col_idx]).strip()
                            if prod_text:
                                # Tách các sản phẩm bằng dấu phẩy hoặc dấu chấm
                                products = [p.strip() for p in re.split(r'[,.;]', prod_text) if p.strip()]
                                all_products.extend(products)
                    
                    if all_products:
                        data.append({
                            "ten_ngan_hang": bank_name,
                            "loai_san_pham": all_products
                        })
                        print(f"✅ {bank_name}: {len(all_products)} products")
                    
        elif ext == 'csv':
            content = file_stream.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                bank = None
                prods = []
                
                # Tìm cột tên ngân hàng
                for key in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank']:
                    if key in row and row[key]:
                        bank = row[key].strip()
                        break
                
                # Tìm tất cả cột sản phẩm
                for key, val in row.items():
                    if key not in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank'] and val:
                        products = [p.strip() for p in re.split(r'[,.;]', str(val)) if p.strip()]
                        prods.extend(products)
                
                if bank and prods:
                    data.append({"ten_ngan_hang": bank, "loai_san_pham": prods})
                    
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(file_stream)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            prompt = f"""Trích xuất danh sách ngân hàng và sản phẩm từ văn bản sau. 
            Trả về JSON array: [{{'ten_ngan_hang': '...', 'loai_san_pham': ['sp1', 'sp2']}}]. 
            Văn bản: {text[:8000]}"""
            raw = call_groq_api(prompt)
            try:
                if isinstance(raw, str):
                    return json.loads(raw), None
                return raw, None
            except:
                return None, "Không thể parse PDF bằng AI"
        else:
            return None, "Định dạng file không hỗ trợ (chỉ hỗ trợ .xlsx, .csv, .pdf)"

        if not data:
            return None, "Không tìm thấy dữ liệu trong file"
            
        return data, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Lỗi parse file: {str(e)}"

@app.route('/api/analyze-upload', methods=['POST'])
def analyze_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "File rỗng"}), 400
        
    print(f"📁 Nhận file: {file.filename}")
    print(f"📊 Content-Type: {file.content_type}")
        
    file_stream = io.BytesIO(file.read())
    results, err = parse_uploaded_file(file_stream, file.filename)
    
    print(f"✅ Kết quả parse: {len(results) if results else 0} ngân hàng")
    if err:
        print(f"❌ Lỗi: {err}")
        return jsonify({"error": err}), 400
    
    if not results:
        return jsonify({"error": "Không parse được dữ liệu"}), 400
    
    # Chuẩn bị data cho AI phân tích
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
    
    print(f"🤖 Calling AI strategy analysis for {len(prepared)} banks...")
    strategy = analyze_strategy(prepared)
            
    return jsonify({
        "status": "success",
        "results": results,
        "strategy": strategy
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
