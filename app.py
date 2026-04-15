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
    return {"status": "ok", "version": "3.3-camel-case"}

def convert_to_camel_case(obj):
    """Chuyển đổi tất cả key trong dict từ snake_case sang Camel_Case"""
    if isinstance(obj, dict):
        return {convert_key(k): convert_to_camel_case(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_camel_case(item) for item in obj]
    else:
        return obj

def convert_key(key):
    """Chuyển snake_case sang Camel_Case (viết hoa chữ cái đầu mỗi từ)"""
    if not isinstance(key, str):
        return key
    
    # Giữ nguyên các key đặc biệt
    if key in ['url', 'extraction_quality']:
        return key
    
    # Chuyển đổi: bank_name -> Bank_name, executive_summary -> Executive_summary
    parts = key.split('_')
    return '_'.join([p.capitalize() for p in parts])

def safe_analysis(item):
    """Normalize data với key chữ hoa để match JavaScript"""
    a = item.get("analysis", {})
    
    # Chuyển đổi strategic_analysis sang Camel_Case
    strategic = a.get("strategic_analysis", {})
    strategic_camel = convert_to_camel_case(strategic) if strategic else {
        "Positioning": "Unknown",
        "Target_segments": [],
        "Key_differentiators": [],
        "Pricing_strategy": "Unknown",
        "Distribution_strategy": "Unknown",
        "Marketing_strategy": "Unknown"
    }
    
    # Chuyển đổi competitive_assessment sang Camel_Case
    competitive = a.get("competitive_assessment", {})
    competitive_camel = convert_to_camel_case(competitive) if competitive else {
        "Strengths": [],
        "Weaknesses": [],
        "Market_position": "Unknown",
        "Competitive_threat_level": "Unknown"
    }
    
    # Chuyển đổi products sang Camel_Case
    products = a.get("products", [])
    products_camel = []
    for p in products:
        if isinstance(p, dict):
            products_camel.append(convert_to_camel_case(p))
        else:
            products_camel.append(p)
    
    return {
        "Bank_name": a.get("bank_name") or "Unknown Bank",
        "Bank_code": a.get("bank_code"),
        "Products": products_camel,
        "Interest_rates": a.get("interest_rates") or {},
        "Promotions": a.get("promotions") or [],
        "Digital_capabilities": a.get("digital_capabilities") or [],
        "Strategic_analysis": strategic_camel,
        "Competitive_assessment": competitive_camel,
        "Product_gaps_vs_market": a.get("product_gaps_vs_market", []),
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
                if idx < len(urls): 
                    time.sleep(2)
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                errors.append(f"{url}: {str(e)}")

        if len(errors) == len(urls) and len(urls) > 0:
            return jsonify({"status": "error", "errors": errors}), 503

        strategy = analyze_strategy(results)
        
        # Chuyển đổi strategy sang Camel_Case
        if isinstance(strategy, dict):
            strategy = convert_to_camel_case(strategy)
        elif isinstance(strategy, str):
            try:
                strategy = json.loads(strategy)
                strategy = convert_to_camel_case(strategy)
            except:
                strategy = {
                    "Executive_summary": "Error parsing strategy",
                    "Competitive_ranking": []
                }

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

# ====================== FILE UPLOAD - KHÔNG DÙNG PANDAS ======================
def parse_uploaded_file(file_stream, filename):
    ext = filename.lower().split('.')[-1]
    data = []

    try:
        if ext in ['xlsx', 'xls']:
            # Đọc Excel bằng openpyxl (không cần pandas)
            from openpyxl import load_workbook
            wb = load_workbook(file_stream)
            ws = wb.active
            
            # Tìm header row
            headers = []
            for cell in ws[1]:
                headers.append(str(cell.value).lower().strip() if cell.value else '')
            
            # Tìm cột cần thiết
            bank_col = None
            prod_col = None
            
            for idx, h in enumerate(headers):
                if h in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank', 'tên ngân hàng']:
                    bank_col = idx
                if h in ['loai_san_pham', 'san_pham', 'products', 'loại sản phẩm']:
                    prod_col = idx
            
            if bank_col is None:
                return None, "Không tìm thấy cột tên ngân hàng (ten_ngan_hang/bank_name)"
            
            # Đọc data
            for row in ws.iter_rows(min_row=2, values_only=True):
                if len(row) > bank_col and row[bank_col]:
                    bank = str(row[bank_col]).strip()
                    prods = []
                    if prod_col is not None and len(row) > prod_col and row[prod_col]:
                        prod_val = row[prod_col]
                        if isinstance(prod_val, str):
                            prods = [x.strip() for x in prod_val.split(',') if x.strip()]
                        else:
                            prods = [str(prod_val)]
                    data.append({"ten_ngan_hang": bank, "loai_san_pham": prods})
                    
        elif ext == 'csv':
            # Đọc CSV thuần
            content = file_stream.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                # Tìm cột tên ngân hàng
                bank = None
                for key in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank', 'tên ngân hàng']:
                    if key in row and row[key]:
                        bank = row[key].strip()
                        break
                
                # Tìm cột sản phẩm
                prods = []
                for key in ['loai_san_pham', 'san_pham', 'products', 'loại sản phẩm']:
                    if key in row and row[key]:
                        prod_val = row[key]
                        prods = [x.strip() for x in str(prod_val).split(',') if x.strip()]
                        break
                
                if bank:
                    data.append({"ten_ngan_hang": bank, "loai_san_pham": prods})
                    
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(file_stream)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            prompt = f"""Trích xuất danh sách ngân hàng từ văn bản sau. 
            Trả về JSON array: [{{'ten_ngan_hang': '...', 'loai_san_pham': []}}]. 
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
        return None, f"Lỗi parse file: {str(e)}"

@app.route('/api/analyze-upload', methods=['POST'])
def analyze_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "File rỗng"}), 400
        
    file_stream = io.BytesIO(file.read())
    results, err = parse_uploaded_file(file_stream, file.filename)
    
    if err: 
        return jsonify({"error": err}), 400
    
    if not results:
        return jsonify({"error": "Không parse được dữ liệu"}), 400
    
    prepared = [{"analysis": {"bank_name": i["ten_ngan_hang"], "products": i["loai_san_pham"]}} for i in results]
    strategy = analyze_strategy(prepared)
    
    # Chuyển đổi strategy sang Camel_Case
    if isinstance(strategy, dict):
        strategy = convert_to_camel_case(strategy)
    elif isinstance(strategy, str):
        try:
            strategy = json.loads(strategy)
            strategy = convert_to_camel_case(strategy)
        except:
            strategy = {
                "Executive_summary": "Error",
                "Competitive_ranking": []
            }
            
    return jsonify(strategy)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
