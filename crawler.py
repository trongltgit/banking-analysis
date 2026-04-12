import requests
from bs4 import BeautifulSoup
import time

def crawl_website(url):
    """
    Enhanced crawler với structured content extraction
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        }

        print(f"      🌐 Fetching {url}...")
        res = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Remove noise elements
        noise_tags = ["script", "style", "nav", "footer", "header", "form", "aside", "iframe", "noscript"]
        for tag in soup(noise_tags):
            tag.decompose()

        # Extract structured content
        title = soup.title.get_text(strip=True) if soup.title else ""
        
        # Meta tags
        meta_desc = ""
        meta_keywords = ""
        for meta in soup.find_all("meta"):
            if meta.get("name") == "description":
                meta_desc = meta.get("content", "")
            if meta.get("name") == "keywords":
                meta_keywords = meta.get("content", "")

        # Headings hierarchy
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")[:3]]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")[:6]]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")[:6]]

        # Product-related sections (common banking patterns)
        product_keywords = ["sản phẩm", "product", "dịch vụ", "service", "tiết kiệm", "savings", 
                           "cho vay", "loan", "thẻ", "card", "bảo hiểm", "insurance"]
        
        product_sections = []
        for keyword in product_keywords:
            elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
            for elem in elements[:3]:
                parent = elem.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if len(text) > 20 and len(text) < 500:
                        product_sections.append(text)

        # Links analysis
        links = [a.get("href", "") for a in soup.find_all("a", href=True)[:20]]
        product_links = [l for l in links if any(k in l.lower() for k in ["product", "service", "san-pham", "dich-vu"])]

        # Main content
        body_text = soup.get_text(separator=" ", strip=True)

        # Build structured content
        full_text = f"""
URL: {url}
TITLE: {title}
META_DESCRIPTION: {meta_desc}
META_KEYWORDS: {meta_keywords}

HEADINGS:
H1: {' | '.join(h1_tags)}
H2: {' | '.join(h2_tags)}
H3: {' | '.join(h3_tags)}

PRODUCT_SECTIONS:
{' | '.join(list(set(product_sections))[:10])}

PRODUCT_LINKS:
{' | '.join(product_links[:10])}

CONTENT:
{body_text}
"""
        
        # Return substantial content for AI analysis
        return full_text[:8000]

    except requests.exceptions.Timeout:
        return f"ERROR_CRAWL_TIMEOUT: {url}"
    except requests.exceptions.RequestException as e:
        return f"ERROR_CRAWL_REQUEST: {url} | {str(e)}"
    except Exception as e:
        return f"ERROR_CRAWL: {url} | {str(e)}"
