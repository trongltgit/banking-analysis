import os
import traceback
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from crawler import crawl_website
from extractor import extract_data
from llm import analyze_strategy

app = Flask(__name__)
# CORS cho phép tất cả origins trong development
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/health")
def health():
    return {"status": "ok", "version": "2.1-pro"}

def safe_analysis(item):
    """Normalize data"""
    a = item.get("analysis", {})
    
    return {
        "bank_name": a.get("bank_name") or "Unknown Bank",
        "bank_code": a.get("bank_code"),
        "products": a.get("products") or [],
        "interest_rates": a.get("interest_rates") or {},
        "promotions": a.get("promotions") or [],
        "digital_capabilities": a.get("digital_capabilities") or [],
        "positioning": a.get("positioning") or "Unknown",
        "strengths": a.get("strengths") or [],
        "weaknesses": a.get("weaknesses") or [],
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

        results = []
        print(f"\n{'='*60}")
        print(f"🚀 DEEP ANALYSIS: {len(urls)} BANKS")
        print(f"{'='*60}\n")

        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] 🔍 {url}")
            
            try:
                # Crawl
                raw = crawl_website(url)
                if raw.startswith("ERROR_CRAWL"):
                    raise Exception(raw)
                
                print(f"      📄 {len(raw)} chars crawled")
                
                # AI Extraction
                extracted = extract_data(raw, url)
                quality = extracted.get("extraction_quality", "unknown")
                product_count = len(extracted.get("analysis", {}).get("products", []))
                
                print(f"      🤖 Quality: {quality} | 📦 Products: {product_count}")

            except Exception as e:
                print(f"      ❌ Error: {str(e)[:100]}")
                # Fallback data
                domain = url.split("//")[-1].split("/")[0].replace("www.", "").upper()
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": domain,
                        "bank_code": None,
                        "products": [],
                        "interest_rates": {},
                        "promotions": [],
                        "digital_capabilities": [],
                        "positioning": "Extraction failed",
                        "strengths": [],
                        "weaknesses": [f"Crawl error: {str(e)[:50]}"]
                    },
                    "extraction_quality": "error"
                }

            results.append(safe_analysis(extracted))

        print(f"\n{'='*60}")
        print("🧠 GENERATING STRATEGY...")
        print(f"{'='*60}\n")

        # Strategy Generation
        try:
            strategy = analyze_strategy(results)
            print("      ✅ Strategy generated")
            
            if isinstance(strategy, str):
                try:
                    strategy = json.loads(strategy)
                except:
                    pass
                    
        except Exception as e:
            print(f"      ❌ Strategy error: {str(e)[:100]}")
            strategy = {
                "executive_summary": "Strategy generation encountered an error. Using competitive analysis fallback.",
                "competitive_landscape": {
                    "market_leader": "Analysis requires retry",
                    "challengers": []
                },
                "strategic_recommendations": {
                    "immediate_actions": [
                        {"action": "Review competitor websites manually", "rationale": "Automated extraction limited"}
                    ]
                },
                "error": str(e)[:100]
            }

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy,
            "meta": {
                "banks_analyzed": len(results),
                "total_products": sum(len(r["products"]) for r in results),
                "analysis_date": "2026-04-12"
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
