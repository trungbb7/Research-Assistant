import os
import sys
import json
import traceback

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

from tools.search_web_urls import search_website_url
from tools.fetch_web_content import fetch_web_content
from tools.get_current_datetime import get_current_datetime
from tools.arxiv_search import arxiv_search
from tools.download_pdf import download_pdf
from tools.save_report import save_report
from tools.llm_utils_tools import (
    generate_plan,
    select_papers,
    check_info_for_research,
    extract_findings,
    compare_papers,
    trends_analysis,
    generate_report,
    write_final_report,
)
from tools.handle_document import (
    retrieve_specific_paper_chunks,
    add_documents,
    retrieve_paper_summaries,
)
from models.state import AgentState
from utils.document_utils import serialize_research_report

load_dotenv()


# openai_api_key = os.getenv("OPENAI_API_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# llm = ChatOpenAI(
#     model="gpt-5-mini",
#     api_key=openai_api_key,
#     temperature=0.2,
# )

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.2,
)

tools = [
    search_website_url,
    fetch_web_content,
    get_current_datetime,
    generate_plan,
    arxiv_search,
    download_pdf,
    add_documents,
    select_papers,
    check_info_for_research,
    retrieve_paper_summaries,
]
tools_node = ToolNode(tools)


llm_with_tools = llm.bind_tools(tools)


def llm_node(state: AgentState):
    messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def route_llm(state: AgentState):
    last_msg = state["messages"][-1]

    if last_msg.tool_calls:
        return "tools"

    if state["completed"]:
        # md_print(serialize_research_report(state["report"]))
        return END

    if state["enough_info"]:
        return "retrieve_chunks"

    return END


def retrieve_chunks_node(state: AgentState):
    paper_ids = state["selected_paper_ids"]
    query = state["query"]

    chunks = retrieve_specific_paper_chunks(query=query, paper_ids=paper_ids)
    return {"chunks": chunks}


def extract_findings_node(state: AgentState):
    query = state["query"]
    chunks = state["chunks"]

    findings = extract_findings(query=query, chunks=chunks)

    return {"findings": findings}


def compare_papers_node(state: AgentState):
    findings = state["findings"]

    comparison_result = compare_papers(findings=findings)

    return {"comparison": comparison_result}


def trends_analysis_node(state: AgentState):
    paper_summaries = state["selected_paper_summaries"]

    trends = trends_analysis(summaries=paper_summaries)

    return {"trends": trends}


def generate_report_node(state: AgentState):
    query = state["query"]
    summaries = state["selected_paper_summaries"]
    findings = state["findings"]
    comparison = state["comparison"]
    trends = state["trends"]

    report = generate_report(
        query=query,
        summaries=summaries,
        findings=findings,
        comparison=comparison,
        trends=trends,
    )

    return {"report": report, "completed": True}


def write_final_report_node(state: AgentState):
    research_report = state["report"]
    final_report = write_final_report(research_report)
    return {"final_report": final_report}


def finalize_node(state: AgentState):
    final_report = state["final_report"]
    save_report(final_report)
    # md_print(final_report)


def run_agent_stream(query):
    workflow = StateGraph(AgentState)

    workflow.add_node("llm", llm_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("retrieve_chunks", retrieve_chunks_node)
    workflow.add_node("extract_findings", extract_findings_node)
    workflow.add_node("compare_papers", compare_papers_node)
    workflow.add_node("trends_analysis", trends_analysis_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("write_final_report", write_final_report_node)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", route_llm)
    workflow.add_edge("tools", "llm")
    workflow.add_edge("retrieve_chunks", "extract_findings")
    workflow.add_edge("extract_findings", "compare_papers")
    workflow.add_edge("compare_papers", "trends_analysis")
    workflow.add_edge("trends_analysis", "generate_report")
    workflow.add_edge("generate_report", "write_final_report")
    workflow.add_edge("write_final_report", "finalize")
    workflow.add_edge("finalize", END)

    app = workflow.compile()

    inputs = {
        "messages": [
            SystemMessage(
                content="""You are a research assistant. You help users research or answer normal queries.
                 For most tasks, get the current date time first.
                 
                 CRITICAL INSTRUCTIONS FOR RESEARCH TASKS:
                 If a task requires research, you must follow the strict step-by-step pipeline. Your primary goal is to gather and ingest the research papers, and then verify if we have enough information.
                 
                 WARNING: You MUST NOT write or generate the final report or summary yourself. The system has specialized downstream nodes that will automatically extract findings, compare papers, analyze trends, and compile the final report. Your role is solely to fetch, download, ingest, select, and check the information.
                 
                 Flow for Research Tasks:
                 1. Call `generate_plan` tool to structure the research tasks.
                 2. Search the internet using `search_website_url` to find the latest updates, models, and paper names.
                 3. Use `arxiv_search` to find relevant scientific papers on arXiv.
                 4. For each relevant paper you want to study, you MUST download its PDF file by calling `download_pdf(url)`.
                    - DO NOT call `fetch_web_content` on PDF files, academic paper URLs, or arXiv PDFs. Only use `download_pdf`.
                 5. For each successfully downloaded PDF file, you MUST ingest it into the database by calling `add_documents(pdf_path, metadata)`.
                    - If pdf files exist, don't ingest them (they have been ingested before)
                 6. After adding documents, you MUST call `select_papers()` to select the relevant papers and populate `selected_paper_ids` in the system state.
                 7. Finally, call `check_info_for_research()` to check if the gathered paper summaries are enough to answer the research query.
                 8. If `check_info_for_research` indicates that the information is NOT enough (enough=False), go back to search for more papers.
                 9. If `check_info_for_research` indicates that the information IS enough (enough=True), you MUST IMMEDIATELY stop calling tools and respond with a simple text message like "I have gathered enough research papers and successfully ingested them. Starting the research extraction and analysis..." without writing the report yourself.
                 """
            ),
            HumanMessage(content=query),
        ],
        "query": query,
        "enough_info": False,
        "completed": False,
    }

    yield {"event": "start", "query": query}

    for output in app.stream(inputs, stream_mode="updates"):
        for node_name, updated_state in output.items():
            yield {"event": "node_start", "node": node_name}

            if updated_state is None:
                yield {"event": "node_end", "node": node_name}
                continue

            if "messages" in updated_state and updated_state["messages"]:
                last_msg = updated_state["messages"][-1]
                if getattr(last_msg, "tool_calls", None):
                    for tool_call in last_msg.tool_calls:
                        args = tool_call["args"]
                        yield {
                            "event": "tool_call",
                            "node": node_name,
                            "tool": tool_call["name"],
                            "arguments": args,
                        }

                content = last_msg.content
                if content:
                    if isinstance(content, list) and content:
                        text_val = (
                            content[0].get("text", "")
                            if isinstance(content[0], dict)
                            else str(content[0])
                        )
                        yield {"event": "log", "node": node_name, "content": text_val}
                    elif not (
                        getattr(last_msg, "tool_calls", None)
                        or getattr(last_msg, "tool_call_id", None)
                    ):
                        yield {"event": "log", "node": node_name, "content": content}
                    else:
                        yield {
                            "event": "log",
                            "node": node_name,
                            "content": "Executing tool...",
                        }

            # Capture other details from state updates
            if "plan" in updated_state and updated_state["plan"]:
                plan_val = updated_state["plan"]
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "plan",
                    "value": plan_val.dict() if hasattr(plan_val, "dict") else plan_val,
                }

            if (
                "selected_paper_ids" in updated_state
                and updated_state["selected_paper_ids"]
            ):
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "selected_paper_ids",
                    "value": updated_state["selected_paper_ids"],
                }

            if "findings" in updated_state and updated_state["findings"]:
                findings_val = updated_state["findings"]
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "findings",
                    "value": [
                        f.dict() if hasattr(f, "dict") else f for f in findings_val
                    ],
                }

            if "comparison" in updated_state and updated_state["comparison"]:
                comp_val = updated_state["comparison"]
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "comparison",
                    "value": comp_val.dict() if hasattr(comp_val, "dict") else comp_val,
                }

            if "trends" in updated_state and updated_state["trends"]:
                trends_val = updated_state["trends"]
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "trends",
                    "value": (
                        trends_val.dict() if hasattr(trends_val, "dict") else trends_val
                    ),
                }

            if "report" in updated_state and updated_state["report"]:
                report_val = updated_state["report"]

                serialized = serialize_research_report(report_val)
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "report",
                    "value": serialized,
                }

            if "final_report" in updated_state and updated_state["final_report"]:
                yield {
                    "event": "state_update",
                    "node": node_name,
                    "key": "final_report",
                    "value": updated_state["final_report"],
                }

            yield {"event": "node_end", "node": node_name}

    yield {"event": "complete"}


def event_stream(query):
    try:
        for update in run_agent_stream(query):
            event_name = update.get("event", "log")
            yield f"event: {event_name}\ndata: {json.dumps(update, ensure_ascii=False)}\n\n"
    except Exception as e:
        err_msg = {
            "event": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
        }
        yield f"event: error\ndata: {json.dumps(err_msg, ensure_ascii=False)}\n\n"
