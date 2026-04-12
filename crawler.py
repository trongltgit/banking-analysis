import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside"]):
            tag.decompose()

        # ---- EXTRACT STRUCTURED CONTENT (IMPORTANT UPGRADE) ----
        title = soup.title.get_text(strip=True) if soup.title else ""

        h1 = " | ".join([h.get_text(strip=True) for h in soup.find_all("h1")[:5]])
        h2 = " | ".join([h.get_text(strip=True) for h in soup.find_all("h2")[:8]])

        meta_desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            meta_desc = meta["content"]

        body_text = soup.get_text(separator=" ", strip=True)

        full_text = f"""
TITLE: {title}

META: {meta_desc}

HEADINGS:
H1: {h1}
H2: {h2}

CONTENT:
{body_text}
"""

        # giữ đủ context cho LLM nhưng không quá dài
        return full_text[:6000]

    except Exception as e:
        return f"ERROR_CRAWL: {url} | {str(e)}"
