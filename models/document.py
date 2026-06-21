from pydantic import BaseModel


class DocumentMetaData(BaseModel):
    title: str
    authors: list[str]
    published: str
    categories: list[str]


class PageDocument(BaseModel):
    page_number: int
    content: str


class Document(BaseModel):
    pages: list[PageDocument]
    metadata: DocumentMetaData
