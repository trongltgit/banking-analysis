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

@app.route("/analyze", methods=["POST"])
def analyze():
    urls = request.json.get("urls", [])

    results = []

    for url in urls:
        if not url.strip():
            continue
        raw = crawl_website(url)
        data = extract_data(raw, url)
        results.append(data)

    strategy = analyze_strategy(results)

    return jsonify({
        "results": results,
        "strategy": strategy
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
