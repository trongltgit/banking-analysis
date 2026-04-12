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

        results = []

        for url in urls:
            if not url or not url.strip():
                continue

            # Crawl
            raw = crawl_website(url)

            # Extract AI
            extracted = extract_data(raw, url)

            results.append(extracted)

        # Strategy AI
        strategy = analyze_strategy(results)

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy
        })

    except Exception as e:
        # 👇 LOG FULL ERROR RA CONSOLE (QUAN TRỌNG)
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
