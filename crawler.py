import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")

        # ❗ CHỈ LẤY TEXT CƠ BẢN (KHÔNG full HTML)
        texts = soup.get_text(separator=" ", strip=True)

        # ❗ GIỚI HẠN SIZE
        return texts[:2000]

    except Exception as e:
        return f"ERROR CRAWL: {str(e)}"
