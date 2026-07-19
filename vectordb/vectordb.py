from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient

from ..embeddings.embedding import dense_embeddings, spare_embeddings

from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
)

client = QdrantClient(url="http://localhost:6333")


def ensure_collection(name: str):
    collections = {c.name for c in client.get_collections().collections}

    if name in collections:
        return

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=len(dense_embeddings.embed_query("test")),
            distance=Distance.COSINE,
        ),
        sparse_vectors_config={"langchain-sparse": SparseVectorParams()},
    )


ensure_collection("paper_chunks")
ensure_collection("paper_summaries")

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
