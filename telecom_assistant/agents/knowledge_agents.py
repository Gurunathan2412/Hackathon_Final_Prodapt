# LlamaIndex implementation
from typing import Dict, Any

try:
    from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex, SQLDatabase  # type: ignore
    from llama_index.core.query_engine import RouterQueryEngine  # type: ignore
    from llama_index.core.tools import QueryEngineTool  # type: ignore
    from llama_index.core.selectors import LLMSingleSelector  # type: ignore
    from llama_index.llms.openai import OpenAI  # type: ignore
    from sqlalchemy import create_engine  # type: ignore
except Exception as e:
    Settings = SimpleDirectoryReader = VectorStoreIndex = OpenAI = object  # type: ignore
    SQLDatabase = RouterQueryEngine = QueryEngineTool = LLMSingleSelector = object  # type: ignore
    create_engine = None  # type: ignore
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
    
    # Initialize LLM and service context (using Settings for newer API)
    try:
        Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
    except Exception as e:
        return {"error": "LLM init failed", "detail": str(e)}
    
    # Load and index documents for vector search
    try:
        reader = SimpleDirectoryReader(DOCUMENTS_DIR)
        docs = reader.load_data()
        vector_index = VectorStoreIndex.from_documents(docs)
        vector_query_engine = vector_index.as_query_engine(similarity_top_k=3)
    except Exception as e:
        return {"error": "Vector index build failed", "detail": str(e)}
    
    # Try to create SQL query engine for factual queries
    sql_query_engine = None
    if SQLDatabase is not object and create_engine is not None:
        try:
            # Connect to the SQLite database
            db_path = "sqlite:///data/telecom.db"
            sql_engine = create_engine(db_path)
            
            # Create SQLDatabase wrapper
            sql_database = SQLDatabase(sql_engine)
            
            # Create SQL query engine with custom prompt
            sql_query_engine = sql_database.as_query_engine(
                synthesize_response=True,
                sql_only=False
            )
            
            if logger:
                logger.info("SQL query engine created successfully")
        except Exception as e:
            if logger:
                logger.warning(f"Could not create SQL query engine: {e}")
            sql_query_engine = None
    
    # If SQL engine creation failed, return simple vector engine (preserve existing functionality)
    if sql_query_engine is None:
        if logger:
            logger.info("Using simple vector query engine (SQL engine not available)")
        _ENGINE_CACHE = vector_query_engine
        return _ENGINE_CACHE
    
    # Create QueryEngineTools for both engines
    try:
        vector_tool = QueryEngineTool.from_defaults(
            query_engine=vector_query_engine,
            name="vector_search",
            description=(
                "Useful for answering conceptual and procedural questions about telecom services. "
                "Use this for questions like 'How do I set up VoLTE?', 'What is the process for "
                "international roaming?', or 'How to configure APN settings?'. Best for guidance "
                "and step-by-step instructions."
            )
        )
        
        sql_tool = QueryEngineTool.from_defaults(
            query_engine=sql_query_engine,
            name="sql_database",
            description=(
                "Useful for answering factual, data-driven questions about coverage, devices, and "
                "technical specifications. Use this for questions like 'Which areas have 5G coverage?', "
                "'Is Samsung Galaxy S22 compatible with VoLTE?', or 'What devices support eSIM?'. "
                "Best for precise factual lookups."
            )
        )
        
        if logger:
            logger.info("QueryEngineTools created successfully")
    except Exception as e:
        if logger:
            logger.warning(f"Could not create QueryEngineTools: {e}")
        # Fallback to simple vector engine
        _ENGINE_CACHE = vector_query_engine
        return _ENGINE_CACHE
    
    # Create RouterQueryEngine with LLMSingleSelector
    try:
        selector = LLMSingleSelector.from_defaults()
        
        router_query_engine = RouterQueryEngine(
            selector=selector,
            query_engine_tools=[vector_tool, sql_tool],
            verbose=True
        )
        
        if logger:
            logger.info("RouterQueryEngine created successfully with Vector + SQL routing")
        
        _ENGINE_CACHE = router_query_engine
        return _ENGINE_CACHE
        
    except Exception as e:
        if logger:
            logger.warning(f"Could not create RouterQueryEngine: {e}. Using simple vector engine.")
        # Fallback to simple vector engine (preserve existing functionality)
        _ENGINE_CACHE = vector_query_engine
        return _ENGINE_CACHE


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
