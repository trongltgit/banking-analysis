import os
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls:
            return jsonify({
                "status": "error",
                "message": "No URLs provided"
            }), 400

        # 🔥 CLEAN INPUT
        urls = [u.strip() for u in urls if u.strip()]

        results = []

        # =========================
        # PROCESS DYNAMIC (NO LIMIT)
        # =========================
        for idx, url in enumerate(urls):
            try:
                print(f"[{idx+1}/{len(urls)}] Processing: {url}")

                raw = crawl_website(url)

                # 🔥 truncate để bảo vệ RAM + LLM
                raw = raw[:2000]

                extracted = extract_data(raw, url)

            except Exception as inner_err:
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": url,
                        "products": [],
                        "interest_rates": "",
                        "promotions": [],
                        "error": str(inner_err)
                    }
                }

            results.append(extracted)

        # =========================
        # STRATEGY (OPTIONAL FAIL SAFE)
        # =========================
        try:
            strategy = analyze_strategy(results)
        except Exception as e:
            strategy = f"Strategy error: {str(e)}"

        return jsonify({
            "status": "success",
            "total": len(results),   # ✅ thêm để frontend dùng
            "results": results,
            "strategy": strategy
        })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
