import uuid
import fitz
from typing import Annotated
from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from qdrant_client import models
from langgraph.prebuilt import InjectedState
from ..models.document import DocumentMetaData, Document, PageDocument
from ..vectordb.vectordb import (
    paper_chunks_retriever,
    paper_summaries_retriever,
    paper_chunks_vectorstore,
    paper_summaries_vectorstore,
)
from .llm_utils_tools import summary_chunks, summary_paper
from ..utils.document_utils import serilize_paper_summary


@tool
def add_documents(
    pdf_path: str,
    metadata: DocumentMetaData,
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Read a PDF file from the given path, chunk it, summarize it, and save chunks and summary to vectordb.
    Also appends the newly created summary to the agent's state.
    """
    try:

        # Check if the paper exists in vectordb
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.title", match=models.MatchValue(metadata.title)
                )
            ]
        )
        existing = paper_summaries_retriever.invoke(
            input=metadata.title,
            config={"search_kwargs": {"filter": search_filter, "k": 1}},
        )
        if existing:
            current_summaries = state.get("paper_summaries", []) or []
            new_summaries = list(current_summaries) + existing

            return Command(
                update={
                    "paper_summaries": new_summaries,
                    "messages": [
                        ToolMessage(
                            content="Paper found in vectordb, use the existing one",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        # Else, insert into vectordb
        # Read PDF content
        doc = fitz.open(pdf_path)
        pages = []
        for i in range(len(doc)):
            page = doc[i]
            page_document = PageDocument(
                content=page.get_text("text"), page_number=i + 1
            )
            pages.append(page_document)

        document = Document(pages=pages, metadata=metadata)

        paper_id = str(uuid.uuid4())
        # Convert to Langchain Document
        lc_docs = []
        for page in document.pages:
            content = page.content
            metadata_dict = {
                "page_number": page.page_number,
                "paper_id": paper_id,
                **document.metadata.model_dump(),
            }
            lc_doc = LangchainDocument(page_content=content, metadata=metadata_dict)
            lc_docs.append(lc_doc)

        # Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100, separators=["\n\n", "\n", " ", ""]
        )
        docs = text_splitter.split_documents(lc_docs)

        # Summary paper
        summaried_chunks = summary_chunks([d.page_content for d in docs])
        paper_summary = summary_paper(summaried_chunks)
        paper_summary_content = serilize_paper_summary(paper_summary)

        # Save paper chunks
        paper_chunks_vectorstore.add_documents(docs)

        # Save paper summary
        new_summary_doc = LangchainDocument(
            page_content=paper_summary_content,
            metadata={
                "paper_id": paper_id,
                **paper_summary.model_dump(),
                **document.metadata.model_dump(),
            },
        )
        paper_summaries_vectorstore.add_documents([new_summary_doc])

        # Get existing summaries and append new one
        current_summaries = state.get("paper_summaries", []) or []
        new_summaries = list(current_summaries) + [new_summary_doc]

        return Command(
            update={
                "paper_summaries": new_summaries,
                "messages": [
                    ToolMessage(
                        content="Insert data into vectordb successfully",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    except Exception as e:
        raise e
        return f"Error while inserting data into vectordb: {str(e)}"


def retrieve_paper_chunks(query: str = "", k=10) -> list[LangchainDocument]:
    """Retrieve paper chunks"""
    return paper_chunks_retriever.invoke(
        input=query, config={"search_kwargs": {"k": k}}
    )


@tool
def retrieve_paper_summaries(
    query: str = "",
    k=10,
    state: Annotated[dict, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = None,
):
    """Retrieve paper summaries and save to state"""
    summaries = paper_summaries_retriever.invoke(
        input=query, config={"search_kwargs": {"k": k}}
    )

    # Get existing summaries and append new summaries
    current_summaries = state.get("paper_summaries", []) or []
    new_summaries = list(current_summaries) + summaries

    return Command(
        update={
            "paper_summaries": new_summaries,
            "messages": [
                ToolMessage(
                    content=f"Successfully retrieved {len(summaries)} paper summaries from database.",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


def retrieve_specific_paper_chunks(
    query: str = "", k=10, paper_ids: list[str] = []
) -> list[LangchainDocument]:
    """Retrieve by specific paper chunks"""

    search_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.paper_id", match=models.MatchAny(paper_ids)
            )
        ]
    )

    docs = paper_chunks_retriever.invoke(
        input=query, config={"search_kwargs": {"k": k, "filter": search_filter}}
    )

    sorted_docs = sorted(docs, key=lambda x: x.metadata.get("paper_id", ""))

    return sorted_docs
