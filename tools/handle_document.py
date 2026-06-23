import uuid
from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..models.document import Document
from ..vectordb.vectordb import paper_chunks_db, paper_summaries_db
from llm_utils_tools import summary_chunks, summary_paper
from ..utils.document_utils import serilize_paper_summary


def add_documents(document: Document):
    """Save paper (Chunks and summary) to vectordb"""
    try:
        paper_id = str(uuid.uuid4())
        # Convert to Langchain Document
        lc_docs = []
        for page in document.pages:
            content = page.content
            metadata = {
                "page_number": page.page_number,
                "paper_id": paper_id,
                **document.metadata.model_dump(),
            }
            lc_doc = LangchainDocument(page_content=content, metadata=metadata)
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
        paper_chunks_db.add_documents(docs)
        # Save paper summary
        paper_summaries_db.add_documents(
            [
                LangchainDocument(
                    page_content=paper_summary_content,
                    metadata={
                        "paper_id": paper_id,
                        **paper_summary.model_dump(),
                        **document.metadata.model_dump(),
                    },
                )
            ]
        )

        return "Insert data into vectordb successfully"
    except:
        return "Error while inserting data into vectordb"


def retrieve_paper_chunks(
    query: str = "", k=5, filter: dict[str, str] = None
) -> list[LangchainDocument]:
    """Retrieve paper chunks"""
    return paper_chunks_db.similarity_search(query, k=k, filter=filter)


def retrieve_paper_summaries(
    query: str = "", k=5, filter: dict[str, str] = None
) -> list[LangchainDocument]:
    """Retrieve paper summaries"""
    return paper_summaries_db.similarity_search(query, k=k, filter=filter)


def retrieve_specific_paper_chunks(
    query: str = "", k=10, paper_ids: list[str] = []
) -> list[LangchainDocument]:
    """Retrieve by specific paper chunks"""
    docs = paper_chunks_db.similarity_search(
        query=query, k=k, filter={"paper_id": {"$in": paper_ids}}
    )

    return docs
