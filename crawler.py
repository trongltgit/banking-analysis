import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    """
    Enhanced crawler - Không cần lxml, dùng html.parser
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        }

        print(f"      🌐 Fetching {url}...")
        res = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        res.raise_for_status()

        # DÙNG html.parser thay vì lxml
        soup = BeautifulSoup(res.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside", "iframe"]):
            tag.decompose()

        # Extract key data
        title = soup.title.get_text(strip=True) if soup.title else ""
        
        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            meta_desc = meta.get("content", "")

        # Headings
        h1_list = [h.get_text(strip=True) for h in soup.find_all("h1")[:3]]
        h2_list = [h.get_text(strip=True) for h in soup.find_all("h2")[:5]]

        # Find product-related content
        product_keywords = ["sản phẩm", "tiết kiệm", "cho vay", "thẻ", "bảo hiểm", "lãi suất"]
        product_texts = []
        
        # Tìm các section có chứa keywords
        for elem in soup.find_all(["div", "section", "article"]):
            text = elem.get_text(strip=True)
            if any(kw in text.lower() for kw in product_keywords) and 50 < len(text) < 800:
                product_texts.append(text[:500])

        body_text = soup.get_text(separator=" ", strip=True)

        full_text = f"""
URL: {url}
TITLE: {title}
META: {meta_desc}
H1: {' | '.join(h1_list)}
H2: {' | '.join(h2_list)}
PRODUCT_SECTIONS: {' | '.join(product_texts[:5])}
CONTENT: {body_text[:4000]}
"""
        return full_text[:6000]

    except Exception as e:
        return f"ERROR_CRAWL: {url} | {str(e)}"
