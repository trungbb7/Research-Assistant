from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from .document import (
    PaperSummary,
    ChunkSummary,
    Finding,
    ComparisionResult,
    TrendAnalysis,
    ResearchPlan,
)


class ResearchState(TypedDict):
    completed: bool
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    research_plan: ResearchPlan
    paper_summary: list[PaperSummary]
    chunks: list[ChunkSummary]
    findings: list[Finding]
    comparison: ComparisionResult
    trends: TrendAnalysis
