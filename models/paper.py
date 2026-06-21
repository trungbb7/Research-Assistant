from pydantic import BaseModel


class Paper(BaseModel):
    title: str
    authors: list[str]
    summary: str
    published: str
    pdf_url: str
    entry_id: str
    categories: list[str]
