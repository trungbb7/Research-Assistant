from ddgs import DDGS


def search_website_url(query: str, max_results: int = 3) -> str:
    """Search website urls for given query"""
    with DDGS() as ddgs:
        results = [r["href"] for r in ddgs.text(query, max_results=max_results)]

    return results
