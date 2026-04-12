import os
import traceback
import json
import time
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
    return {"status": "ok", "version": "2.2-stable"}

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
        "strategic_analysis": a.get("strategic_analysis", {
            "positioning": "Unknown",
            "target_segments": [],
            "key_differentiators": [],
            "pricing_strategy": "Unknown",
            "distribution_strategy": "Unknown",
            "marketing_strategy": "Unknown"
        }),
        "competitive_assessment": a.get("competitive_assessment", {
            "strengths": [],
            "weaknesses": [],
            "market_position": "Unknown",
            "competitive_threat_level": "Unknown"
        }),
        "url": item.get("url"),
        "extraction_quality": item.get("extraction_quality", "unknown"),
        "error": item.get("error")
    }

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        urls = data.get("urls", [])

        if not urls:
            return jsonify({"status": "error", "message": "No URLs provided"}), 400

        # Giới hạn số URL để tránh rate limit
        if len(urls) > 5:
            urls = urls[:5]
            print(f"⚠️ Limited to 5 URLs to avoid rate limits")

        results = []
        print(f"\n{'='*60}")
        print(f"🚀 DEEP ANALYSIS: {len(urls)} BANKS")
        print(f"{'='*60}\n")

        # Xử lý TUẦN TỰ (không parallel) để tránh rate limit
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] 🔍 {url}")
            
            try:
                # Crawl
                raw = crawl_website(url)
                if raw.startswith("ERROR_CRAWL"):
                    print(f"      ⚠️ Crawl failed: {raw[:50]}")
                
                # Delay trước khi gọi AI
                time.sleep(1)
                
                # AI Extraction
                extracted = extract_data(raw, url)
                quality = extracted.get("extraction_quality", "unknown")
                product_count = len(extracted.get("analysis", {}).get("products", []))
                
                print(f"      📄 {len(raw)} chars | 🤖 {quality} | 📦 {product_count} products")
                
                # Delay sau mỗi lần gọi API
                time.sleep(1.5)
                
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:80]}")
                domain = url.split("//")[-1].split("/")[0].replace("www.", "").upper()
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": domain,
                        "products": [],
                        "strategic_analysis": {"positioning": f"Error: {str(e)[:30]}"},
                        "competitive_assessment": {"strengths": [], "weaknesses": ["Processing error"]}
                    },
                    "extraction_quality": "error"
                }

            results.append(safe_analysis(extracted))

        print(f"\n{'='*60}")
        print("🧠 GENERATING STRATEGY...")
        print(f"{'='*60}\n")

        # Delay trước khi gọi strategy
        time.sleep(2)
        
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
            print(f"      ❌ Strategy error: {str(e)[:80]}")
            strategy = {
                "executive_summary": "Strategy generation failed due to rate limits. Please try with fewer banks.",
                "competitive_ranking": [{"rank": i+1, "bank": r.get("bank_name", "Unknown"), "position": "Unknown"} for i, r in enumerate(results)],
                "strategic_recommendations": {
                    "overall_strategy": "Retry with 2-3 banks maximum",
                    "immediate_actions": ["Wait 1 minute", "Reduce number of URLs"]
                }
            }

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy,
            "meta": {
                "banks_analyzed": len(results),
                "total_products": sum(len(r["products"]) for r in results),
                "note": "Rate limiting may affect results quality"
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
