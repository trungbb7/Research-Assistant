from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


openai_embedding = OpenAIEmbeddings(model="text-embedding-3-small")
