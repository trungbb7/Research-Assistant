from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import FastEmbedSparse
from dotenv import load_dotenv

load_dotenv()


dense_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
spare_embeddings = FastEmbedSparse("Qdrant/bm25")
