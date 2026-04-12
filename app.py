from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy
import os

app = Flask(__name__)
CORS(app)

# =========================
# HOME PAGE (UI DASHBOARD)
# =========================
@app.route("/")
def home():
    return render_template("dashboard.html")


# =========================
# API: ANALYZE URLS
# =========================
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        urls = data.get("urls", [])

        results = []

        for url in urls:
            if not url or not url.strip():
                continue

            # Crawl website
            raw = crawl_website(url)

            # Extract bằng AI
            extracted = extract_data(raw, url)

            results.append(extracted)

        # Phân tích chiến lược
        strategy = analyze_strategy(results)

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================
# HEALTH CHECK (RENDER)
# =========================
@app.route("/health")
def health():
    return {"status": "ok"}


# =========================
# RUN SERVER (RENDER)
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
