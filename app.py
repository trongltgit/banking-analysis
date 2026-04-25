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
from llm import analyze_strategy, call_ai_api, clean_json

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from openpyxl import load_workbook
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False

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
    return {"status": "ok", "version": "5.0-anthropic"}


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls:
            return jsonify({"status": "error", "message": "Vui lòng nhập ít nhất 1 URL"}), 400

        urls = urls[:4]  # Giới hạn 4 URLs

        cache_key = get_cache_key(urls)
        if cache_key in _cache:
            print("📦 Returning cached result")
            return jsonify(_cache[cache_key])

        results = []
        errors = []

        for idx, url in enumerate(urls, 1):
            try:
                print(f"\n{'='*50}")
                print(f"🔍 [{idx}/{len(urls)}] Processing: {url}")

                raw = crawl_website(url)

                if not raw:
                    raise Exception("Không thể crawl website (trả về None)")

                print(f"📄 Content length: {len(raw)} chars")

                extracted = extract_data(raw, url)
                results.append(extracted)

                print(f"✅ Done: {extracted['analysis'].get('bank_name')} "
                      f"({extracted['extraction_quality']}, "
                      f"{len(extracted['analysis'].get('products', []))} products)")

                # Delay giữa các request
                if idx < len(urls):
                    time.sleep(2)

            except Exception as e:
                print(f"❌ Error processing {url}: {str(e)}")
                errors.append(f"{url}: {str(e)}")

                # Tạo error entry thay vì bỏ qua hoàn toàn
                from extractor import create_error_response, get_bank_info
                bank_info = get_bank_info(url)
                results.append(create_error_response(bank_info, url))

        print(f"\n📊 Processed {len(results)} banks, generating strategy...")

        # Chỉ phân tích strategy với kết quả không lỗi
        valid_results = [r for r in results if r.get("extraction_quality") != "error"]

        if valid_results:
            strategy = analyze_strategy(valid_results)
        else:
            strategy = {
                "executive_summary": "Tất cả websites đều không thể crawl trực tiếp. "
                                     "Kết quả dựa trên knowledge base.",
                "competitive_ranking": [],
                "strategic_recommendations": {"overall_strategy": "Vui lòng thử lại."}
            }

        response_data = {
            "status": "success",
            "results": results,
            "strategy": strategy,
            "meta": {
                "total": len(urls),
                "successful": len(valid_results),
                "from_knowledge_base": len([r for r in results if r.get("source") == "knowledge_base"]),
                "errors": len(errors)
            }
        }

        # Cache kết quả trong 10 phút
        _cache[cache_key] = response_data
        # Xóa cache cũ nếu > 20 entries
        if len(_cache) > 20:
            oldest = list(_cache.keys())[0]
            del _cache[oldest]

        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


def parse_uploaded_file(file_stream, filename):
    """Parse file XLSX, CSV, hoặc PDF"""
    ext = filename.lower().split('.')[-1]
    data = []

    try:
        if ext in ['xlsx', 'xls']:
            if not HAS_XLSX:
                return None, "openpyxl chưa được cài đặt"

            wb = load_workbook(file_stream)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))

            if len(rows) < 2:
                return None, "File không đủ dữ liệu (cần ít nhất 2 dòng)"

            # Tìm header row
            header_idx = None
            header_map = {}
            for i, row in enumerate(rows[:5]):
                row_lower = [str(c).strip().lower() if c else "" for c in row]
                for col_i, cell in enumerate(row_lower):
                    if cell in ['ten_ngan_hang', 'ngân hàng', 'bank', 'ngan_hang']:
                        header_idx = i
                        header_map['bank'] = col_i
                        break
                if header_idx is not None:
                    break

            if header_idx is None:
                # Giả sử cột đầu là tên ngân hàng
                header_idx = 0
                header_map['bank'] = 0

            for i in range(header_idx + 1, len(rows)):
                row = rows[i]
                if not row or not row[header_map.get('bank', 0)]:
                    continue
                bank_name = str(row[header_map.get('bank', 0)]).strip()
                all_products = []
                for col_idx in range(len(row)):
                    if col_idx == header_map.get('bank', 0):
                        continue
                    if row[col_idx]:
                        products = [p.strip() for p in re.split(r'[;,\n]', str(row[col_idx])) if p.strip()]
                        all_products.extend(products)
                if bank_name:
                    data.append({"ten_ngan_hang": bank_name, "loai_san_pham": all_products})

        elif ext == 'csv':
            content = file_stream.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                bank = None
                prods = []
                for key in row:
                    key_lower = key.lower().strip()
                    if key_lower in ['ten_ngan_hang', 'ngan_hang', 'bank_name', 'bank', 'ngân hàng']:
                        bank = row[key].strip()
                    elif row[key]:
                        products = [p.strip() for p in re.split(r'[;,]', str(row[key])) if p.strip()]
                        prods.extend(products)
                if bank and prods:
                    data.append({"ten_ngan_hang": bank, "loai_san_pham": prods})

        elif ext == 'pdf':
            if not HAS_PDF:
                return None, "PyPDF2 chưa được cài đặt"
            reader = PyPDF2.PdfReader(file_stream)
            text = "".join([page.extract_text() or "" for page in reader.pages])
            prompt = (
                f"Trích xuất danh sách ngân hàng và sản phẩm từ văn bản sau. "
                f"Trả về JSON array: [{{'ten_ngan_hang': '...', 'loai_san_pham': ['sp1', 'sp2']}}]. "
                f"Văn bản: {text[:5000]}"
            )
            raw = call_ai_api(prompt)
            parsed = clean_json(raw)
            if parsed and isinstance(parsed, list):
                return parsed, None
            return None, "Không thể trích xuất dữ liệu từ PDF"
        else:
            return None, f"Định dạng .{ext} không được hỗ trợ (chỉ xlsx, csv, pdf)"

        return data if data else None, None if data else "Không tìm thấy dữ liệu trong file"

    except Exception as e:
        return None, f"Lỗi đọc file: {str(e)}"


@app.route('/api/analyze-upload', methods=['POST'])
def analyze_upload():
    if 'file' not in request.files:
        return jsonify({"error": "Không có file được upload"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "File rỗng"}), 400

    file_stream = io.BytesIO(file.read())
    results, err = parse_uploaded_file(file_stream, file.filename)

    if err:
        return jsonify({"error": err}), 400
    if not results:
        return jsonify({"error": "Không parse được dữ liệu từ file"}), 400

    # Chuyển thành format phân tích
    prepared = []
    for item in results:
        prepared.append({
            "url": "",
            "analysis": {
                "bank_name": item["ten_ngan_hang"],
                "bank_code": item["ten_ngan_hang"][:3].upper(),
                "products": [
                    {"name": p, "category": guess_category(p), "features": []}
                    for p in item["loai_san_pham"]
                ],
                "promotions": [],
                "digital_capabilities": [],
                "interest_rates": {},
                "strategic_analysis": {},
                "competitive_assessment": {}
            },
            "extraction_quality": "good",
            "source": "file_upload"
        })

    strategy = analyze_strategy(prepared)
    return jsonify({
        "status": "success",
        "results": prepared,
        "strategy": strategy
    })


def guess_category(product_name):
    """Đoán danh mục sản phẩm từ tên"""
    name_lower = product_name.lower()
    if any(w in name_lower for w in ['tiết kiệm', 'gửi', 'savings', 'deposit']):
        return 'SAVINGS'
    if any(w in name_lower for w in ['vay', 'tín dụng', 'loan', 'credit']):
        return 'LOAN'
    if any(w in name_lower for w in ['thẻ', 'card', 'visa', 'mastercard']):
        return 'CARD'
    if any(w in name_lower for w in ['app', 'mobile', 'digital', 'internet', 'online']):
        return 'DIGITAL'
    if any(w in name_lower for w in ['bảo hiểm', 'insurance']):
        return 'INSURANCE'
    if any(w in name_lower for w in ['đầu tư', 'quỹ', 'trái phiếu', 'investment']):
        return 'INVESTMENT'
    return 'OTHER'


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
