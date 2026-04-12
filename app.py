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
            return jsonify({"status": "error", "message": "No URLs"}), 400

        results = []

        for idx, url in enumerate(urls):
            print(f"[{idx+1}/{len(urls)}] Processing:", url)

            try:
                raw = crawl_website(url)
                raw = raw[:2000]

                extracted = extract_data(raw, url)

                # ✅ ENSURE STRUCTURE ALWAYS SAFE
                if "analysis" not in extracted:
                    extracted = {
                        "url": url,
                        "analysis": {
                            "bank_name": url.split("//")[-1],
                            "products": [],
                            "interest_rates": "",
                            "promotions": []
                        }
                    }

            except Exception as e:
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": url.split("//")[-1],
                        "products": [],
                        "interest_rates": "",
                        "promotions": [],
                        "error": str(e)
                    }
                }

            results.append(extracted)

        # 🔥 SAFE STRATEGY HANDLING
        try:
            strategy = analyze_strategy(results)

            # nếu trả string JSON → convert nhẹ
            if isinstance(strategy, str):
                strategy = strategy

        except Exception as e:
            strategy = {
                "insights": ["Strategy engine error"],
                "recommendations": [],
                "strength_leader": "",
                "weakness_leader": "",
                "error": str(e)
            }

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
