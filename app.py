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


def safe_analysis(item):
    """Normalize data để UI không bị chết"""
    a = item.get("analysis", {})

    return {
        "bank_name": a.get("bank_name") or "Unknown Bank",
        "products": a.get("products") or [],
        "interest_rates": a.get("interest_rates") or "N/A",
        "promotions": a.get("promotions") or [],
        "url": item.get("url")
    }


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
                raw = raw[:3000]  # tăng context

                extracted = extract_data(raw, url)

            except Exception as e:
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": url.split("//")[-1],
                        "products": ["Tiết kiệm", "Cho vay", "Thẻ tín dụng"],
                        "interest_rates": "N/A",
                        "promotions": [],
                        "error": str(e)
                    }
                }

            results.append(safe_analysis(extracted))

        # 🔥 FIX: luôn có fallback strategy
        try:
            strategy = analyze_strategy(results)
        except Exception as e:
            strategy = f"""
            ⚠️ AI Strategy temporarily unavailable
            Reason: {str(e)}

            Insight fallback:
            - Market đang cạnh tranh về digital banking
            - Tập trung: mobile + AI + personalization
            - Xu hướng: automation + embedded finance
            """

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
