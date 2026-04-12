import requests


def crawl_website(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(url, headers=headers, timeout=10)

        # Check HTTP status
        if response.status_code != 200:
            return f"Error: HTTP {response.status_code} when accessing {url}"

        return response.text

    except requests.exceptions.Timeout:
        return f"Error: Timeout when accessing {url}"

    except requests.exceptions.RequestException as e:
        return f"Error crawling {url}: {str(e)}"
