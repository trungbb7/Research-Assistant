import os
import re
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from .utils.common_utils import md_print
from .tools.search_web_urls import search_website_url
from .tools.fetch_web_content import fetch_web_content
from .tools.get_current_datetime import get_current_datetime
from .tools.arxiv_search import arxiv_search
from .tools.download_pdf import download_pdf
from .tools.read_pdf import read_pdf
from .tools.llm_utils_tools import (
    generate_plan,
    select_papers,
    check_info_for_research,
    extract_findings,
    compare_papers,
    trends_analysis,
    generate_report,
)
from .tools.handle_document import retrieve_specific_paper_chunks, add_documents
from .models.state import AgentState

load_dotenv()
llm = None

flatform = os.getenv("LLM_FLATFORM")
if flatform == "DEEPSEEK":
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=deepseek_api_key,
        base_url="https://api.deepseek.com",
        temperature=0.2,
    )
elif flatform == "OPENAI":
    print("da vao openai")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    llm = ChatOpenAI(
        model="gpt-5-mini",
        api_key=openai_api_key,
        temperature=0.2,
    )

tools = [
    # search_website_url,
    # fetch_web_content,
    get_current_datetime,
    generate_plan,
    arxiv_search,
    download_pdf,
    read_pdf,
    add_documents,
    select_papers,
    check_info_for_research,
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
        md_print(state["report"])
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
    paper_summaries = state["paper_summaries"]

    trends = trends_analysis(summaries=paper_summaries)

    return {"trends": trends}


def generate_report_node(state: AgentState):
    query = state["query"]
    summaries = state["paper_summaries"]
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


def run_agent(query):
    workflow = StateGraph(AgentState)

    workflow.add_node("llm", llm_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("retrieve_chunks", retrieve_chunks_node)
    workflow.add_node("extract_findings", extract_findings_node)
    workflow.add_node("compare_papers", compare_papers_node)
    workflow.add_node("trends_analysis", trends_analysis_node)
    workflow.add_node("generate_report", generate_report_node)

    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", route_llm)
    workflow.add_edge("tools", "llm")
    workflow.add_edge("retrieve_chunks", "extract_findings")
    workflow.add_edge("extract_findings", "compare_papers")
    workflow.add_edge("compare_papers", "trends_analysis")
    workflow.add_edge("compare_papers", "generate_report")
    workflow.add_edge("generate_report", "llm")

    app = workflow.compile()

    inputs = {
        "messages": [
            SystemMessage(
                content="You are a research assistant, help people research or answer normal queries."
            ),
            HumanMessage(content=query),
        ],
        "query": query,
        "enough_info": False,
        "completed": False,
    }

    for output in app.stream(inputs, stream_mode="updates"):
        for node_name, updated_state in output.items():
            print(f"Node: {node_name}")

            if "messages" in updated_state and updated_state["messages"]:
                last_msg = updated_state["messages"][-1]
                if getattr(last_msg, "tool_calls", None):
                    for tool_call in last_msg.tool_calls:
                        args = ", ".join(
                            [f"{k}={v}" for k, v in tool_call["args"].items()]
                        )
                        print(f"Tool call: {tool_call["name"]}, args: {args}")
                        continue

                content = last_msg.content
                if isinstance(content, list) and content:
                    md_print(content[0]["text"])
                elif not (
                    getattr(last_msg, "tool_calls", None)
                    or getattr(last_msg, "tool_call_id", None)
                ):
                    md_print(content)
                else:
                    print(f"Log: {content[:200]}{'...' if len(content) > 200 else ''}")
