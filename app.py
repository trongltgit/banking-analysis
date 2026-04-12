import os
import traceback
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy

app = Flask(__name__)
CORS(app)


# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return render_template("dashboard.html")


# =========================
# HEALTH CHECK
# =========================
@app.route("/health")
def health():
    return {"status": "ok"}


# =========================
# ANALYZE API
# =========================
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

        # 🔥 HARD LIMIT để tránh OOM
        urls = urls[:2]

        results = []

        for url in urls:
            if not url or not url.strip():
                continue

            try:
                print(f"Processing: {url}")

                # =================
                # STEP 1: CRAWL
                # =================
                raw = crawl_website(url)

                if not raw:
                    raise Exception("Empty content")

                # 🔥 GIẢM SIZE MẠNH
                raw = raw[:800]

                # =================
                # STEP 2: EXTRACT AI
                # =================
                extracted = extract_data(raw, url)

            except Exception as inner_err:
                print("INNER ERROR:", inner_err)

                extracted = {
                    "url": url,
                    "analysis": f"Error: {str(inner_err)}"
                }

            results.append(extracted)

        # =================
        # STEP 3: STRATEGY (OPTIONAL)
        # =================
        strategy = "Skipped"

        try:
            strategy = analyze_strategy(results)
        except Exception as e:
            print("STRATEGY ERROR:", e)
            strategy = f"Strategy error: {str(e)}"

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy
        })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# RUN LOCAL / RENDER
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
