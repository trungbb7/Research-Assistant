import os
import sys
import torch
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from ..config import basePath

# Allow forcing device via env variable
env_device = os.getenv("EMBEDDING_DEVICE")
if env_device:
    device = torch.device(env_device)
else:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_name = "BAAI/bge-m3"
model_kwargs = {"device": str(device)}
encode_kwargs = {"normalize_embeddings": True}
local_model_path = basePath / "MLModels" / "bge-m3"
local_model_path.mkdir(parents=True, exist_ok=True)

try:
    bgem3_embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
        cache_folder=str(local_model_path),
    )
except Exception as e:
    if "cuda" in str(device):
        print("CUDA initialization failed (possibly OOM). Falling back to CPU for embeddings.", file=sys.stderr)
        model_kwargs["device"] = "cpu"
        bgem3_embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
            cache_folder=str(local_model_path),
        )
    else:
        raise e

