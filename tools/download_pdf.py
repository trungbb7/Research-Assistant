import requests
from pathlib import Path
from langchain_core.tools import tool


@tool
def download_pdf(url: str):
    "Download pdf file from given url"
    try:
        save_dir = Path("../data/papers")
        save_dir.mkdir(parents=True, exist_ok=True)

        file_name = url.split("/")[-1]
        if not url.endswith(".pdf"):
            file_name += ".pdf"

        file_path = save_dir / file_name

        if file_path.exists():
            return f"Existing file path founded: {str(file_path)}"

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        return str(file_path)
    except:
        return "Error while downloading pdf file"
