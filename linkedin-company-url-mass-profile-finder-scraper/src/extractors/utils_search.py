thonimport logging
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

def search_bing(query: str, timeout: int = 10, user_agent: str = "") -> List[Dict[str, str]]:
    """
    Perform a simple Bing search and return a list of results.

    Each result is:
        {
            "title": ...,
            "url": ...,
            "snippet": ...
        }

    This implementation is intentionally lightweight and may be affected by
    rate limiting or bot protection in real-world use. It is sufficient as an
    example of a production-style scraper.
    """
    headers = {
        "User-Agent": user_agent
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
           "AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    params = {"q": query}
    url = "https://www.bing.com/search"

    logging.debug("Issuing Bing request: %s", url)

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logging.error("Bing request failed: %s", exc)
        raise

    soup = BeautifulSoup(resp.text, "html.parser")
    results: List[Dict[str, str]] = []

    # Bing search result blocks are often contained in <li class="b_algo">
    for li in soup.select("li.b_algo"):
        a = li.find("a")
        if not a or not a.get("href"):
            continue

        title = a.get_text(strip=True)
        href = a["href"]

        snippet_el = li.find("p")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

        results.append(
            {
                "title": title,
                "url": href,
                "snippet": snippet,
            }
        )

    logging.debug("Parsed %d results from Bing for query '%s'", len(results), query)
    return results

def is_probable_linkedin_company_url(url: str) -> bool:
    """
    Heuristic to decide whether a URL is likely a LinkedIn company profile.
    """
    if "linkedin.com" not in url:
        return False

    lowered = url.split("?")[0].lower()
    if any(path in lowered for path in ("/company/", "/school/", "/showcase/")):
        return True

    return False