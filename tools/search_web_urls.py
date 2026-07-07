from ddgs import DDGS
from langchain_core.tools import tool


@tool
def search_website_url(query: str, max_results: int = 3) -> str:
    """Search website urls for given query"""
    try:
        with DDGS() as ddgs:
            results = [r["href"] for r in ddgs.text(query, max_results=max_results)]

        return results
    except Exception as e:
        return f"Error while search website url: {e}"
