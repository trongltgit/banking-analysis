import os
import traceback
import json
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
    return {"status": "ok", "version": "2.0-pro"}

def safe_analysis(item):
    """Normalize data để UI không bị chết"""
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
        print(f"🚀 STARTING DEEP ANALYSIS FOR {len(urls)} BANKS")
        print(f"{'='*60}\n")

        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] 🔍 Processing: {url}")
            
            try:
                # Crawl with enhanced extraction
                raw = crawl_website(url)
                print(f"      📄 Crawled {len(raw)} chars")
                
                # Deep AI extraction
                extracted = extract_data(raw, url)
                quality = extracted.get("extraction_quality", "unknown")
                print(f"      🤖 Extraction quality: {quality}")
                
                product_count = len(extracted.get("analysis", {}).get("products", []))
                print(f"      📦 Products found: {product_count}")

            except Exception as e:
                print(f"      ❌ Error: {str(e)}")
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": url.split("//")[-1].split("/")[0].replace("www.", "").upper(),
                        "bank_code": None,
                        "products": [],
                        "interest_rates": {},
                        "promotions": [],
                        "digital_capabilities": [],
                        "positioning": "Error in extraction",
                        "strengths": [],
                        "weaknesses": [f"Extraction failed: {str(e)}"]
                    },
                    "extraction_quality": "error"
                }

            results.append(safe_analysis(extracted))

        print(f"\n{'='*60}")
        print("🧠 GENERATING STRATEGIC ANALYSIS...")
        print(f"{'='*60}\n")

        # AI Strategy Generation
        try:
            strategy = analyze_strategy(results)
            print("      ✅ Strategy generated successfully")
            
            # Ensure strategy is dict not string
            if isinstance(strategy, str):
                try:
                    strategy = json.loads(strategy)
                except:
                    pass
                    
        except Exception as e:
            print(f"      ❌ Strategy error: {str(e)}")
            strategy = {
                "error": str(e),
                "executive_summary": "Strategy generation failed. Using fallback analysis.",
                "competitive_landscape": {"market_leader": "Analysis pending"},
                "strategic_recommendations": {
                    "immediate_actions": ["Review extraction quality", "Retry with specific competitor data"]
                }
            }

        response_data = {
            "status": "success",
            "results": results,
            "strategy": strategy,
            "meta": {
                "banks_analyzed": len(results),
                "total_products": sum(len(r["products"]) for r in results),
                "timestamp": "2026-04-12"
            }
        }

        print(f"\n{'='*60}")
        print("✅ ANALYSIS COMPLETE")
        print(f"{'='*60}\n")

        return jsonify(response_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
