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


class ChunkSummary(BaseModel):
    key_points: list[str]
    methods: list[str]
    datasets: list[str]
    metrics: list[str]


class PaperSummary(BaseModel):
    title: str
    problem: str
    methodology: str
    datasets: list[str]
    key_contributions: list[str]
    strengths: list[str]
    weaknesses: list[str]
    conclution: str
