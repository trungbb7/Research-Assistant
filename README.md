# AI Research Assistant

A LangGraph-powered AI Research Assistant designed to automate the process of academic research. It creates plans, queries academic databases, downloads/ingests PDFs, performs RAG (Retrieval-Augmented Generation) using a hybrid vector store, and generates comprehensive comparative reports.

---

## Features

- **Agentic LangGraph Workflow:** Autonomous orchestration of research plans, web searches, paper downloads, ingestion, and multi-step report generation.
- **Hybrid Retrieval (RAG):** Combines OpenAI dense embeddings (`text-embedding-3-small`) with BM25 sparse embeddings (`FastEmbedSparse`) in a Qdrant vector database.
- **Academic Search & Ingestion:** Searches arXiv and general web databases, downloads papers as PDFs, and chunks/stores them automatically.
- **Streaming Web Interface:** Simple Flask frontend that displays live updates and logs from the LangGraph execution using Server-Sent Events (SSE).
- **Structured Reports:** Produces structured Markdown reports covering research findings, paper comparisons, and trend analysis.

---

## Prerequisites

- **Python 3.11+**
- **Qdrant Vector Database** (or Docker to run it)
- **API Keys:** OpenAI API key (for embeddings) and DeepSeek API key (for the LLM).

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/trungbb7/Research-Assistant.git
cd ai-agent
```

### 2. Set Up Virtual Environment & Dependencies

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```ini
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key
LLM_PLATFORM=OPENAI
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## Running the Application

### Option A: Running Locally

1. **Start Qdrant Vector DB** (via Docker):

   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

2. **Start the Flask Application**:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://localhost:5000`.

---

### Option B: Running with Docker Compose

To spin up both the Flask application and the Qdrant instance together:

```bash
docker-compose up --build
```

Access the application at `http://localhost:5000`.
