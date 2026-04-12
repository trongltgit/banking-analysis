import requests
from bs4 import BeautifulSoup

def crawl_website(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Tăng timeout lên 10s vì web ngân hàng thường load chậm
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Loại bỏ các thành phần rác để LLM không bị rối
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()

        texts = soup.get_text(separator=" ", strip=True)

        # Tăng giới hạn lên 4000 ký tự để lấy đủ thông tin lãi suất
        return texts[:4000]

    except Exception as e:
        return f"ERROR CRAWL ({url}): {str(e)}"
