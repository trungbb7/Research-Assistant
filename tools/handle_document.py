from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..models.document import Document
from ..vectordb.vectordb import vector_db


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

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", " ", ""]
        )
        docs = text_splitter.split_documents(lc_docs)
        vector_db.add_documents(docs)

        return "Thêm dữ liệu vào vectordb thành công"
    except:
        return "Đã xảy ra lỗi khi thêm dữ liệu và vectordb"


def retrieve_document(query: str, k=5, filter: dict[str, str] = {}):
    return vector_db.similarity_search(query, k=k, filter=filter)
