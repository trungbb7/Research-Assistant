import os
from typing import Annotated
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langchain_core.documents import Document as LangchainDocument
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from ..models.document import (
    ChunkSummary,
    PaperSummary,
    Finding,
    ComparisionResult,
    TrendAnalysis,
    ResearchReport,
    Plan,
    PaperSelectionResult,
    CheckInfoResult,
)

load_dotenv()


openai_api_key = os.getenv("OPENAI_API_KEY")

summary_llm = ChatOpenAI(
    model="gpt-4.1-nano",
    api_key=openai_api_key,
    temperature=0.2,
)

reasoning_llm = ChatOpenAI(
    model="gpt-5-nano",
    api_key=openai_api_key,
    temperature=0.2,
)


@tool
def generate_plan(
    query: str,
):
    """Generate plan for query"""
    PROMPT = """
    Generate plan for query

    Identify:
    - topic
    - tasks
    - need research or not
    - is research or normal query

    Query:
    {query}
    """

    structured_llm = reasoning_llm.with_structured_output(Plan)
    plan = structured_llm.invoke(PROMPT.format(query=query))

    return plan.model_dump_json()


@tool
def check_info_for_research(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Check if agent have enough information (from retrieved paper summaries) to start research"""
    PROMPT = """
    Check if agent have enough information (from retrieved paper summaries) to start research about query:

    Query:
    {query}

    Retrieved paper summaries:
    {summaries}
    """

    structured_llm = reasoning_llm.with_structured_output(CheckInfoResult)
    summaries_str = "\n\n".join(
        [summary.model_dump_json() for summary in state["paper_summaries"]]
    )
    response = structured_llm.invoke(
        PROMPT.format(query=state["query"], summaries=summaries_str)
    )

    return Command(
        update={
            "enough_info": response.enough,
            "messages": [
                ToolMessage(
                    content=f"Check info result: enough={response.enough}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


def summary_chunks(chunks: list[str]):
    prompt = """
    Summary chunk in paper
    Extract:
    - Key points
    - Methods
    - Datasets
    - Metrics

    Chunk: {chunk}
    """
    structured_llm = summary_llm.with_structured_output(ChunkSummary)
    summaried_chunks = []
    for chunk in chunks:
        summary = structured_llm.invoke(prompt.format(chunk=chunk))
        summaried_chunks.append(summary)
    return summaried_chunks


def summary_paper(summaried_chunks: list[ChunkSummary]):
    prompt = """
    Summary paper from summaried chunks:

    Summaried chunks:
    {summaried_chunks}
    """

    structured_llm = summary_llm.with_structured_output(PaperSummary)
    summaried_chunks_str = "\n\n".join(
        [chunk.model_dump_json() for chunk in summaried_chunks]
    )
    out = structured_llm.invoke(prompt.format(summaried_chunks=summaried_chunks_str))
    return out


@tool
def select_papers(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Filter paper (from paper summaries) that relative to query"""

    PROMPT = """
    Select paper ids relative to query:

    Query:
    {query}

    Paper summaries:
    {summaries}
    """

    structured_llm = reasoning_llm.with_structured_output(PaperSelectionResult)
    paper_summaries = state["paper_summaries"]
    query = state["query"]
    summaries_str = "\n\n".join(
        [summary.model_dump_json() for summary in paper_summaries]
    )
    response = structured_llm.invoke(
        PROMPT.format(query=query, summaries=summaries_str)
    )

    paper_ids = response.paper_ids

    reduced_paper_summaries = []
    for paper_summary in paper_summaries:
        print(f"Metadata: {paper_summary.metadata}")
        if paper_summary.metadata.get("paper_id") in paper_ids:
            reduced_paper_summaries.append(paper_summary)

    return Command(
        update={
            "selected_paper_ids": paper_ids,
            "paper_summaries": reduced_paper_summaries,
            "messages": [
                ToolMessage(
                    content=f"Selected paper IDs: {paper_ids}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


def extract_findings(query: str, chunks: list[LangchainDocument]):
    prompt = """
    You are a research analyst

    Question:
    {query}

    Paper chunks:
    {chunks}

    Extract:
    - method
    - datasets
    - key results
    - strengths
    - limitations
    """

    structured_llm = reasoning_llm.with_structured_output(Finding)
    findings = []
    paper_ids = list(set([chunk.metadata.get("paper_id") for chunk in chunks]))
    paper_chunks_dict = {
        paper_id: [
            chunk.page_content
            for chunk in chunks
            if chunk.metadata.get("paper_id") == paper_id
        ]
        for paper_id in paper_ids
    }
    for _, paper_chunks in paper_chunks_dict.items():
        chunks_str = "\n\n".join(paper_chunks)

        response = structured_llm.invoke(prompt.format(query=query, chunks=chunks_str))
        findings.append(response)

    return findings


def compare_papers(findings: list[Finding]):
    PROMPT = """
    Compare the following research findings

    Identify:
    - similarities
    - differences
    - best methods
    - tradeoffs

    Findings:
    {findings}
    """

    structured_llm = reasoning_llm.with_structured_output(ComparisionResult)
    findings_str = "\n\n".join([finding.model_dump_json() for finding in findings])
    response = structured_llm.invoke(PROMPT.format(findings=findings_str))
    return response


def trends_analysis(summaries: list[LangchainDocument]):
    PROMPT = """
    Analyze trends across papers

    Identify:
    - major trends
    - emerging directions
    - common limitation
    - future research opportunities

    Paper summaries:
    {summaries}
    """

    structured_llm = reasoning_llm.with_structured_output(TrendAnalysis)
    summaries_str = "\n\n".join([summary.model_dump_json() for summary in summaries])
    response = structured_llm.invoke(PROMPT.format(summaries=summaries_str))
    return response


def generate_report(
    query: str,
    summaries: list[LangchainDocument],
    findings: list[Finding],
    comparison: ComparisionResult,
    trends: TrendAnalysis,
):
    PROMPT = """
    Generate a professional research report

    Question:
    {query}

    Comparison:
    {comparison}

    Trends:
    {trends}

    Findings:
    {findings}

    Summaries:
    {summaries}
    """

    structured_llm = reasoning_llm.with_structured_output(ResearchReport)
    findings_str = "\n\n".join([finding.model_dump_json() for finding in findings])
    summaries_str = "\n\n".join([summary.model_dump_json() for summary in summaries])

    response = structured_llm.invoke(
        PROMPT.format(
            query=query,
            comparison=comparison,
            trends=trends,
            findings=findings_str,
            summaries=summaries_str,
        )
    )
    return response
