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
    paper_id: str
    key_points: list[str]
    methods: list[str]
    datasets: list[str]
    metrics: list[str]


class PaperSummary(BaseModel):
    paper_id: str
    title: str
    problem: str
    methodology: str
    datasets: list[str]
    key_contributions: list[str]
    strengths: list[str]
    weaknesses: list[str]
    conclution: str


class PaperSelectionResult(BaseModel):
    paper_ids: list[str]


class Finding(BaseModel):
    paper_id: str
    method: str
    datasets: list[str]
    results: list[str]
    strengths: list[str]
    limitations: list[str]


class ComparisionResult(BaseModel):
    similarities: list[str]
    differences: list[str]
    best_methods: list[str]
    tradeoffs: list[str]


class TrendAnalysis(BaseModel):
    major_trend: list[str]
    emerging_directions: list[str]
    common_limitations: list[str]
    feature_researchs: list[str]


class ResearchReport(BaseModel):
    title: str
    overview: str
    comparision: str
    trends: str
    key_findings: str
    conclustion: str
    references: list[str]


class Plan(BaseModel):
    topic: str
    tasks: list[str]
    need_research: bool
    is_normal: bool


class CheckInfoResult(BaseModel):
    enough: bool
