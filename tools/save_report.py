# from pydantic import Ano
from config import basePath
from datetime import datetime
import uuid


def save_report(report: str):
    str_time = datetime.now().strftime("%Y%m%d%H%M%S")
    str_uuid = uuid.uuid4()
    file_name = f"{str_time}_{str_uuid}.md"

    save_dir = basePath / "data" / "reports"
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / file_name

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report)
