# import chromadb
# from langchain_chroma import Chroma
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient

# from ..embeddings.bgem3 import bgem3_embeddings
from ..embeddings.embedding import dense_embeddings, spare_embeddings

db = QdrantVectorStore()

# client = chromadb.PersistentClient("chroma_db")
client = QdrantClient("qdrant_storage")

paper_chunks_vectorstore = QdrantVectorStore(
    client=client,
    collection_name="paper_chunks",
    embedding=dense_embeddings,
    sparse_embedding=spare_embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
)

paper_summaries_vectorstore = QdrantVectorStore(
    client=client,
    collection_name="paper_summaries",
    embedding=dense_embeddings,
    sparse_embedding=spare_embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
)

paper_chunks_retriever = paper_chunks_vectorstore.as_retriever()
paper_summaries_retriever = paper_summaries_vectorstore.as_retriever()

# research_memory_db = QdrantVectorStore(
#     client=client,
#     collection_name="research_memory",
#     embedding=dense_embeddings,
#     sparse_embedding=spare_embeddings,
#     retrieval_mode=RetrievalMode.HYBRID
# )
