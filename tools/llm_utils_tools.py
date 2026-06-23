import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from ..models.document import (
    ChunkSummary,
    PaperSummary,
    Finding,
    ComparisionResult,
    TrendAnalysis,
    ResearchReport,
    ResearchPlan,
)

load_dotenv()


deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.2,
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
    structured_llm = llm.with_structured_output(ChunkSummary)
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

    structured_llm = llm.with_structured_output(PaperSummary)
    summaried_chunks_str = "\n\n".join(
        [chunk.model_dump_json() for chunk in summaried_chunks]
    )
    out = structured_llm.invoke(prompt.format(summaried_chunks=summaried_chunks_str))
    return out


def extract_findings(query: str, chunks: list[ChunkSummary]):
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

    structured_llm = llm.with_structured_output(Finding)
    chunks_str = "\n\n".join([chunk.model_dump_json() for chunk in chunks])
    response = structured_llm.invoke(prompt.format(query=query, chunks=chunks_str))
    return response


def compare_paper(findings: list[Finding]):
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

    structured_llm = llm.with_structured_output(ComparisionResult)
    findings_str = "\n\n".join([finding.model_dump_json() for finding in findings])
    response = structured_llm.invoke(PROMPT.format(findings=findings_str))
    return response


def trend_analysis(summaries: list[PaperSummary]):
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

    structured_llm = llm.with_structured_output(ComparisionResult)
    summaries_str = "\n\n".join([summary.model_dump_json() for summary in summaries])
    response = structured_llm.invoke(PROMPT.format(summaries=summaries_str))
    return response


def generate_report(
    query: str,
    comparison: ComparisionResult,
    trends: TrendAnalysis,
    findings: list[Finding],
    summaries: list[PaperSummary],
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

    structured_llm = llm.with_structured_output(ResearchReport)
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


def generate_research_plan(query: str):
    PROMPT = """
    Generate research plan for query

    Query:
    {query}
    """

    structured_llm = llm.with_structured_output(ResearchPlan)
    response = structured_llm.invoke(PROMPT.format(query=query))
    return response
