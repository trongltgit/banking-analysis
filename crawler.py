import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        return soup.get_text(separator=" ", strip=True)

    except Exception as e:
        return f"Error: {str(e)}"
