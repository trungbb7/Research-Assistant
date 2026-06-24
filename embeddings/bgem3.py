import torch
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from ..config import basePath

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = "cuda"

model_name = "BAAI/bge-m3"

model_kwargs = {"device": device}
encode_kwargs = {"normalize_embeddings": True}
local_model_path = basePath / "MLModels" / "bge-m3"
local_model_path.mkdir(parents=True, exist_ok=True)
print(local_model_path)
print(str(local_model_path))

bgem3_embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    cache_folder=str(local_model_path),
)
