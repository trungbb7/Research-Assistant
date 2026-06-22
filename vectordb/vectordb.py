import chromadb
from langchain_chroma import Chroma
from ..embeddings.bgem3 import bgem3_embeddings

client = chromadb.PersistentClient("chroma_db")

vector_db = Chroma(
    client=client,
    collection_name="knowledge_base",
    embedding_function=bgem3_embeddings,
)
