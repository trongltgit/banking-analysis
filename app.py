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
    return {"status": "ok", "version": "3.0-deep-ai"}

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
        "product_gaps_vs_market": a.get("product_gaps_vs_market", []),
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

        # Giới hạn 4 URLs để tránh timeout
        if len(urls) > 4:
            urls = urls[:4]

        results = []
        errors = []
        
        print(f"\n{'='*60}")
        print(f"🚀 DEEP AI ANALYSIS: {len(urls)} BANKS")
        print(f"{'='*60}\n")

        # Xử lý tuần tự với delay
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] 🔍 {url}")
            
            try:
                # Crawl
                raw = crawl_website(url)
                crawl_status = "✅" if not raw.startswith("ERROR_CRAWL") else "⚠️"
                print(f"      {crawl_status} Crawled {len(raw)} chars")
                
                # Delay trước AI
                time.sleep(2)
                
                # AI Extraction - KHÔNG try-catch để lỗi được báo ra
                extracted = extract_data(raw, url)
                
                quality = extracted.get("extraction_quality", "unknown")
                product_count = len(extracted.get("analysis", {}).get("products", []))
                
                print(f"      ✅ AI Analysis: {quality} | {product_count} products")
                
                # Delay sau AI
                time.sleep(2)
                
            except Exception as e:
                error_msg = str(e)
                print(f"      ❌ AI Analysis failed: {error_msg[:80]}")
                errors.append(f"{url}: {error_msg}")
                
                # Vẫn tạo structure nhưng đánh dấu lỗi rõ ràng
                domain = url.split("//")[-1].split("/")[0].replace("www.", "").upper()
                extracted = {
                    "url": url,
                    "analysis": {
                        "bank_name": f"{domain} (LỖI: {error_msg[:30]})",
                        "products": [],
                        "strategic_analysis": {"positioning": f"Error: {error_msg[:50]}"},
                        "competitive_assessment": {"strengths": [], "weaknesses": [error_msg]}
                    },
                    "extraction_quality": "error"
                }

            results.append(safe_analysis(extracted))

        # Nếu tất cả đều lỗi, báo lỗi tổng
        if len(errors) == len(urls):
            return jsonify({
                "status": "error",
                "message": "Tất cả các ngân hàng đều phân tích thất bại",
                "errors": errors,
                "suggestion": "Có thể do rate limit Groq API. Vui lòng đợi 1 phút và thử lại với ít URL hơn (2-3)."
            }), 503

        print(f"\n{'='*60}")
        print("🧠 GENERATING STRATEGY...")
        print(f"{'='*60}\n")

        # Delay trước strategy
        time.sleep(3)
        
        # Strategy Generation
        try:
            strategy = analyze_strategy(results)
            print("      ✅ Strategy generated")
            
            if isinstance(strategy, str):
                strategy = json.loads(strategy)
                    
        except Exception as e:
            print(f"      ❌ Strategy failed: {str(e)[:80]}")
            # Strategy lỗi không fail cả request, chỉ báo trong response
            strategy = {
                "executive_summary": f"Strategy generation error: {str(e)[:100]}. Các phân tích ngân hàng riêng lẻ vẫn hợp lệ.",
                "competitive_ranking": [],
                "strategic_recommendations": {
                    "overall_strategy": "Error in strategy synthesis",
                    "immediate_actions": ["Review individual bank analysis below", "Retry strategy generation later"]
                }
            }

        return jsonify({
            "status": "success",
            "results": results,
            "strategy": strategy,
            "errors": errors if errors else None,
            "meta": {
                "banks_analyzed": len(results),
                "successful": len([r for r in results if r["extraction_quality"] != "error"]),
                "failed": len(errors),
                "total_products": sum(len(r["products"]) for r in results)
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc() if os.environ.get("DEBUG") else None
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
