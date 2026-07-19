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


# openai_api_key = os.getenv("OPENAI_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# summary_llm = ChatOpenAI(
#     model="gpt-5-nano",
#     api_key=openai_api_key,
#     temperature=0.2,
# )

# reasoning_llm = ChatOpenAI(
#     model="gpt-5-mini",
#     api_key=openai_api_key,
#     temperature=0.2,
# )

summary_llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.2,
    extra_body={"thinking": {"type": "disabled"}},
)

reasoning_llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.2,
    extra_body={"thinking": {"type": "disabled"}},
)


@tool
def generate_plan(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
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

    structured_llm = reasoning_llm.with_structured_output(
        Plan, method="function_calling"
    )
    plan = structured_llm.invoke(PROMPT.format(query=query))

    return Command(
        update={
            "plan": plan,
            "messages": [
                ToolMessage(
                    content=f"Generated plan",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


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

    structured_llm = reasoning_llm.with_structured_output(
        CheckInfoResult, method="function_calling"
    )
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


def summary_chunks(chunks: list[str], paper_id: str = ""):
    try:
        prompt = """
        Summary chunk in paper
        Extract:
        - Key points
        - Methods
        - Datasets
        - Metrics

        Chunk: {chunk}
        """
        structured_llm = summary_llm.with_structured_output(
            ChunkSummary, method="function_calling"
        )
        if not chunks:
            return []

        prompts = [prompt.format(chunk=chunk) for chunk in chunks]
        summaried_chunks = structured_llm.batch(
            prompts,
            config={
                "max_concurrency": 3,
            },
        )

        for summary in summaried_chunks:
            summary.paper_id = paper_id

        return summaried_chunks
    except:
        return []


def summary_paper(summaried_chunks: list[ChunkSummary], paper_id: str = ""):
    prompt = """
    Summary paper from summaried chunks:

    Summaried chunks:
    {summaried_chunks}
    """

    structured_llm = summary_llm.with_structured_output(
        PaperSummary, method="function_calling"
    )
    summaried_chunks_str = "\n\n".join(
        [chunk.model_dump_json() for chunk in summaried_chunks]
    )
    out = structured_llm.invoke(prompt.format(summaried_chunks=summaried_chunks_str))
    out.paper_id = paper_id
    return out


@tool
def select_papers(
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Filter papers (from paper summaries) that relative to query"""

    PROMPT = """
    Select list paper ids of papers from paper summaries relative to query:
    Note: Should use multiple papers to compare, extract information, methodology,...

    Query:
    {query}

    Paper summaries:
    {summaries}
    """

    structured_llm = reasoning_llm.with_structured_output(
        PaperSelectionResult, method="function_calling"
    )
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
        if paper_summary.metadata.get("paper_id") in paper_ids:
            reduced_paper_summaries.append(paper_summary)

    return Command(
        update={
            "selected_paper_ids": paper_ids,
            "selected_paper_summaries": reduced_paper_summaries,
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

    Extract the following information.

    IMPORTANT:
    - Every field that contains multiple items MUST be returned as a JSON array.
    - Do NOT return a single string containing numbered items.
    - Each result must be a separate item in the list.

    Required fields:
    - method: list of methods
    - datasets: list of datasets
    - results: list of key results
    - strengths: list of strengths
    - limitations: list of limitations
    """

    structured_llm = reasoning_llm.with_structured_output(
        Finding, method="function_calling"
    )
    paper_ids = list(set([chunk.metadata.get("paper_id") for chunk in chunks]))
    paper_chunks_dict = {
        paper_id: [
            chunk.page_content
            for chunk in chunks
            if chunk.metadata.get("paper_id") == paper_id
        ]
        for paper_id in paper_ids
    }

    batch_inputs = []
    ordered_paper_ids = []
    for paper_id, paper_chunks in paper_chunks_dict.items():
        chunks_str = "\n\n".join(paper_chunks)
        batch_inputs.append(prompt.format(query=query, chunks=chunks_str))
        ordered_paper_ids.append(paper_id)

    if not batch_inputs:
        return []

    findings = structured_llm.batch(batch_inputs)

    for paper_id, finding in zip(ordered_paper_ids, findings):
        finding.paper_id = paper_id

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

    structured_llm = reasoning_llm.with_structured_output(
        ComparisionResult, method="function_calling"
    )
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

    structured_llm = reasoning_llm.with_structured_output(
        TrendAnalysis, method="function_calling"
    )
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

    structured_llm = reasoning_llm.with_structured_output(
        ResearchReport, method="function_calling"
    )
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


def write_final_report(report: ResearchReport):
    str_report = report.model_dump_json()

    PROMPT = """
    Generate final report from research report as markdown format

    Report:
    {report}
    """

    response = reasoning_llm.invoke(PROMPT.format(report=report))
    return response.content
