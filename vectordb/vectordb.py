import chromadb
from langchain_chroma import Chroma
from ..embeddings.bgem3 import bgem3_embeddings

client = chromadb.PersistentClient("chroma_db")

paper_chunks_db = Chroma(
    client=client,
    collection_name="paper_chunks",
    embedding_function=bgem3_embeddings,
)

paper_summaries_db = Chroma(
    client=client,
    collection_name="paper_summaries",
    embedding_function=bgem3_embeddings,
)
