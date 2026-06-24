from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document as LangchainDocument
from .document import Finding, ComparisionResult, TrendAnalysis, Plan, ResearchReport


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    query: str
    research_plan: Plan
    enough_info: bool
    selected_paper_ids: list[str]
    paper_summaries: list[LangchainDocument]
    chunks: list[LangchainDocument]
    findings: list[Finding]
    comparison: ComparisionResult
    trends: TrendAnalysis
    report: ResearchReport
    completed: bool
