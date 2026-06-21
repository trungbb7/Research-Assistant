import os
import re
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
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

from .utils import md_print

load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")


@tool
def search_website_url(query: str, max_results: int = 3) -> str:
    """Search website urls for given query"""
    with DDGS() as ddgs:
        results = [r["href"] for r in ddgs.text(query, max_results=max_results)]

    return results


@tool
def fetch_web_content(urls: list[str]) -> str:
    """Fetch web content for given urls"""
    try:
        results = []

        for url in urls:
            response = requests.get(url)

            if response.status_code != 200:
                results.append(
                    f"Không thể truy cập trang {url}, http status: {response.status_code}"
                )

            soup = BeautifulSoup(response.content, "html.parser")

            for element in soup(
                [
                    "script",
                    "style",
                    "nav",
                    "footer",
                    "header",
                    "aside",
                    "noscript",
                    "svg",
                    "form",
                ]
            ):
                element.decompose()

            elements = soup.find_all(["h1", "h2", "h3", "h4", "p", "td", "div"])
            valid_text = []
            for el in elements:
                text = el.get_text().strip()
                if not text:
                    continue

                if el.name == "div":
                    if len(el.find_all("div")) > 2:
                        continue

                    if len(text) < 60:
                        continue

                clean_text = re.sub(r"\s+", " ", text)
                if not clean_text in valid_text:
                    valid_text.append(clean_text)

            final_article = "\n".join(valid_text)
            results.append(f"{url} ->\n{final_article}")

        return "\n---Article seperator----\n".join(results)

    except:
        return f"Đã xảy ra lỗi khi lấy dữ liệu từ url: {url}"


@tool
def get_current_datetime() -> str:
    """Get current datetime"""
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M:%S")


tools = [search_website_url, fetch_web_content, get_current_datetime]
tools_node = ToolNode(tools)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.2,
)
llm_with_tools = llm.bind_tools(tools)


def llm_node(state: AgentState):
    messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def route_llm(state: AgentState):
    last_msg = state["messages"][-1]

    if last_msg.tool_calls:
        return "tools"

    return END


def run_agent(query):
    workflow = StateGraph(AgentState)

    workflow.add_node("llm", llm_node)
    workflow.add_node("tools", tools_node)

    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", route_llm)
    workflow.add_edge("tools", "llm")

    app = workflow.compile()

    inputs = {"messages": [HumanMessage(content=query)]}

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
                    # print(content[0]['text'])
                    md_print(content[0]["text"])
                elif not (
                    getattr(last_msg, "tool_calls", None)
                    or getattr(last_msg, "tool_call_id", None)
                ):
                    md_print(content)
                else:
                    print(f"Log: {content[:200]}{'...' if len(content) > 200 else ''}")
