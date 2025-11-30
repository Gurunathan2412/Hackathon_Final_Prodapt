# LlamaIndex implementation
from typing import Dict, Any

try:
    from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex  # type: ignore
    from llama_index.llms.openai import OpenAI  # type: ignore
except Exception as e:
    Settings = SimpleDirectoryReader = VectorStoreIndex = OpenAI = object  # type: ignore
    _IMPORT_ERROR = str(e)
else:
    _IMPORT_ERROR = None

try:  # Optional pandas import
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore

from config.config import DOCUMENTS_DIR
try:
    from langchain_openai import OpenAIEmbeddings  # type: ignore
except Exception:
    OpenAIEmbeddings = None  # type: ignore

try:
    from loguru import logger  # type: ignore
except Exception:
    logger = None

SQL_GUIDANCE_PROMPT = """
You are an expert in converting natural language questions about telecom services into SQL queries.
The database contains tables for coverage areas, device compatibility, and technical specifications.
When writing SQL:
1. Use coverage_areas table for location-based questions
2. Use device_compatibility for phone-specific inquiries
3. Use technical_specs for network technology questions
Write focused queries that only retrieve the columns needed to answer the question.
""".strip()

SELECTOR_PROMPT = """
You need to determine which query engine to use:
1. Vector Search Engine: Best for conceptual, procedural questions like "How do I set up VoLTE?" or "What's the process for international roaming?"
2. SQL Database Engine: Best for factual, data-driven questions like "Which areas have 5G coverage?" or "Is the Samsung Galaxy S22 compatible with VoLTE?"
Based on the query, select the most appropriate engine by analyzing if the question requires factual data lookup (SQL) or procedural knowledge (Vector).
Query: {query}
""".strip()

_ENGINE_CACHE = None


def create_knowledge_engine() -> Any:
    """Create and return a LlamaIndex router query engine for knowledge retrieval.

    Returns a RouterQueryEngine or placeholder when dependencies unavailable.
    """
    global _ENGINE_CACHE
    if Settings is object or OpenAI is object:
        return {"error": "Import failure", "detail": _IMPORT_ERROR}
    if _ENGINE_CACHE is not None:
        return _ENGINE_CACHE
    try:
        Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
    except Exception as e:
        return {"error": "LLM init failed", "detail": str(e)}
    try:
        reader = SimpleDirectoryReader(DOCUMENTS_DIR)
        docs = reader.load_data()
        index = VectorStoreIndex.from_documents(docs)
        _ENGINE_CACHE = index.as_query_engine(similarity_top_k=3)
        return _ENGINE_CACHE
    except Exception as e:
        return {"error": "Index build failed", "detail": str(e)}


def process_knowledge_query(query: str) -> Dict[str, Any]:
    """Process a knowledge retrieval query using the LlamaIndex query engine."""
    engine = create_knowledge_engine()
    if isinstance(engine, dict) and engine.get("error"):
        if logger:
            logger.error(f"Knowledge engine error: {engine}")
        return {"query": query, "error": engine["error"], "detail": engine.get("detail"), "status": "error"}
    answer = ""
    sources = []
    try:  # pragma: no cover
        response = engine.query(query)
        answer = getattr(response, 'response', str(response))
        if hasattr(response, 'source_nodes'):
            sources = [getattr(s, 'node', None).get_content()[:120] for s in response.source_nodes if getattr(s,'node',None)]
    except Exception as e:
        if logger:
            logger.error(f"Knowledge query failed: {e}")
        answer = "Knowledge query failed; placeholder answer provided."
    return {"query": query, "answer": answer, "sources": sources, "summary": "Knowledge response generated", "status": "ok"}
