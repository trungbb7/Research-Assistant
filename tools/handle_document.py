from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..models.document import Document
from ..vectordb.vectordb import paper_chunks_db, paper_summaries_db
from llm_utils_tools import summary_chunks, summary_paper
from ..utils.document_utils import serilize_paper_summary


def add_documents(document: Document):
    try:
        # Convert to Langchain Document
        lc_docs = []
        for page in document.pages:
            content = page.content
            metadata = {
                "page_number": page.page_number,
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
                        **paper_summary.model_dump(),
                        **document.metadata.model_dump(),
                    },
                )
            ]
        )

        return "Thêm dữ liệu vào vectordb thành công"
    except:
        return "Đã xảy ra lỗi khi thêm dữ liệu và vectordb"


def retrieve_document(query: str, k=5, filter: dict[str, str] = {}):
    return vector_db.similarity_search(query, k=k, filter=filter)
