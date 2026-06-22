import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from ..models.document import ChunkSummary, PaperSummary

load_dotenv()


deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key=deepseek_api_key,
    base_url="https://api.deepseek.com",
    temperature=0.2,
)


def summary_chunks(chunks: list[str]):
    prompt = """
    Tóm tắt đoạn trong paper
    Trích xuất:
    - Key points
    - Methods
    - Datasets
    - Metrics

    Chunk: {chunk}
    """
    structured_llm = llm.with_structured_output(ChunkSummary)
    summaried_chunks = []
    for chunk in chunks:
        summary = structured_llm.invoke(prompt.format(chunk=chunk))
        summaried_chunks.append(summary)
    return summaried_chunks


def summary_paper(summaried_chunks: list[ChunkSummary]):
    prompt = """
    Tạo bản tóm tác paper từ các chunk được tóm tắt sau:

    Summaried chunks:
    {summaried_chunks}
    """

    structured_llm = llm.with_structured_output(PaperSummary)
    summaried_chunks_str = "\n\n".join(
        [chunk.model_dump_json() for chunk in summaried_chunks]
    )
    out = structured_llm.invoke(prompt.format(summaried_chunks=summaried_chunks_str))
    return out
