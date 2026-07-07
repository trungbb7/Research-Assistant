import chromadb
from langchain_chroma import Chroma

# from ..embeddings.bgem3 import bgem3_embeddings
from ..embeddings.openai_embedding import openai_embedding

client = chromadb.PersistentClient("chroma_db")

paper_chunks_db = Chroma(
    client=client,
    collection_name="paper_chunks",
    embedding_function=openai_embedding,
)

paper_summaries_db = Chroma(
    client=client,
    collection_name="paper_summaries",
    embedding_function=openai_embedding,
)

research_memory_db = Chroma(
    client=client,
    collection_name="research_memory",
    embedding_function=openai_embedding,
)
