import re
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool


@tool
def fetch_web_content(urls: list[str]) -> str:
    """Fetch web content for given urls"""
    try:
        results = []

        for url in urls:
            response = requests.get(url)

            if response.status_code != 200:
                results.append(
                    f"Không thể truy cập trang {url}, http status: {response.status_code}"
                )

            soup = BeautifulSoup(response.content, "html.parser")

            for element in soup(
                [
                    "script",
                    "style",
                    "nav",
                    "footer",
                    "header",
                    "aside",
                    "noscript",
                    "svg",
                    "form",
                ]
            ):
                element.decompose()

            elements = soup.find_all(["h1", "h2", "h3", "h4", "p", "td", "div"])
            valid_text = []
            for el in elements:
                text = el.get_text().strip()
                if not text:
                    continue

                if el.name == "div":
                    if len(el.find_all("div")) > 2:
                        continue

                    if len(text) < 60:
                        continue

                clean_text = re.sub(r"\s+", " ", text)
                if not clean_text in valid_text:
                    valid_text.append(clean_text)

            final_article = "\n".join(valid_text)
            results.append(f"{url} ->\n{final_article}")

        return "\n---Article seperator----\n".join(results)

    except:
        return f"Error while fetching data from url: {url}"
