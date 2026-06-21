import requests
from pathlib import Path


def download_pdf(url: str):
    try:
        save_dir = Path("../data/papers")
        save_dir.mkdir(parents=True, exist_ok=True)

        file_name = url.split("/")[-1]
        if not url.endswith(".pdf"):
            file_name += ".pdf"

        file_path = save_dir / file_name

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        return str(file_path)
    except:
        return "Đã xảy ra lỗi khi tải file pdf"
