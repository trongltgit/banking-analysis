import requests
from bs4 import BeautifulSoup


def crawl_website(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(url, headers=headers, timeout=5)

        # 🔥 CHẶN HTML quá lớn
        if len(res.text) > 500_000:  # >500KB
            return res.text[:1000]

        soup = BeautifulSoup(res.text, "html.parser")

        texts = []

        # 🔥 CHỈ lấy ít thôi
        for tag in soup.find_all(["title", "h1", "h2"]):
            txt = tag.get_text(strip=True)
            if txt:
                texts.append(txt)

        return " ".join(texts)[:1000]

    except Exception as e:
        return f"Error: {str(e)}"
