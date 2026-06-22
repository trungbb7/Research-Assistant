import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

device = os.getenv("device", "cpu")

model_name = "BAAI/bge-m3"

model_kwargs = {"device": device}
encode_kwargs = {"normalize_embeddings": True}

bgem3_embeddings = HuggingFaceEmbeddings(
    model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
)
