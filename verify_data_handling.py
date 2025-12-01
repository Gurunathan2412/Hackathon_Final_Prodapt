"""
Comprehensive verification of data handling, vector storage, and document ingestion
"""
import sqlite3
from pathlib import Path
import sys

print("=" * 80)
print("COMPREHENSIVE DATA HANDLING VERIFICATION")
print("=" * 80)

# 1. Check ChromaDB structure
print("\n### 1. CHROMADB VECTOR DATABASE ###")
print("-" * 80)
chroma_db = Path("telecom_assistant/data/chromadb/chroma.sqlite3")
if chroma_db.exists():
    conn = sqlite3.connect(str(chroma_db))
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"✓ ChromaDB found with {len(tables)} tables:")
    for table in tables:
        print(f"    • {table[0]}")
        
    # Check embeddings count
    try:
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        count = cursor.fetchone()[0]
        print(f"\n✓ Total embeddings stored: {count}")
    except:
        print("\n✓ No embeddings table or different schema")
    
    # Check collections
    try:
        cursor.execute("SELECT * FROM collections")
        collections = cursor.fetchall()
        print(f"\n✓ Collections: {len(collections)}")
        for col in collections:
            print(f"    • Collection: {col}")
    except:
        print("\n✓ No collections table or different schema")
    
    conn.close()
else:
    print("❌ ChromaDB not found!")

# 2. Check document files
print("\n### 2. DOCUMENT FILES IN KNOWLEDGE BASE ###")
print("-" * 80)
docs_path = Path("telecom_assistant/data/documents")
if docs_path.exists():
    docs = list(docs_path.glob("*.txt")) + list(docs_path.glob("*.md")) + list(docs_path.glob("*.pdf"))
    print(f"✓ Documents directory exists with {len(docs)} files:")
    total_size = 0
    for doc in docs:
        size = doc.stat().st_size
        total_size += size
        print(f"    • {doc.name:45s} {size:>8,} bytes")
    print(f"\n✓ Total knowledge base size: {total_size:,} bytes ({total_size/1024:.1f} KB)")
else:
    print("❌ Documents directory not found!")

# 3. Check LlamaIndex engine cache
print("\n### 3. LLAMAINDEX ENGINE STATUS ###")
print("-" * 80)
sys.path.insert(0, 'telecom_assistant')
try:
    from agents.knowledge_agents import _ENGINE_CACHE, create_knowledge_engine
    
    if _ENGINE_CACHE is not None:
        print(f"✓ Engine already cached: {type(_ENGINE_CACHE).__name__}")
    else:
        print("⚠ Engine not yet cached (will be created on first query)")
        print("  Creating engine now...")
        engine = create_knowledge_engine()
        if isinstance(engine, dict) and 'error' in engine:
            print(f"❌ Engine creation failed: {engine.get('error')}")
            print(f"   Detail: {engine.get('detail')}")
        else:
            print(f"✓ Engine created successfully: {type(engine).__name__}")
            
except ImportError as e:
    print(f"❌ Cannot import knowledge_agents: {e}")

# 4. Check if vectors are persistent or in-memory
print("\n### 4. VECTOR STORAGE MECHANISM ###")
print("-" * 80)
print("Based on code analysis:")
print("\n📚 LlamaIndex (knowledge_agents.py):")
print("  • Uses: VectorStoreIndex.from_documents()")
print("  • Storage: IN-MEMORY (recreated on each app start)")
print("  • Source: SimpleDirectoryReader(DOCUMENTS_DIR)")
print("  • Caching: Engine cached in _ENGINE_CACHE after first creation")
print("  • Re-indexing: Requires app restart or cache invalidation")

print("\n📦 LangChain/ChromaDB (document_loader.py):")
print("  • Uses: Chroma.from_texts()")
print("  • Storage: PERSISTENT (data/chromadb/)")
print("  • Database: chroma.sqlite3 + vector data in subdirectories")
print("  • Caching: Vector store cached in _vector_store_cached")
print("  • Re-indexing: Requires calling build_vector_store(persist=True)")

# 5. Data flow summary
print("\n### 5. DATA FLOW FOR KNOWLEDGE QUERIES ###")
print("-" * 80)
print("""
QUERY FLOW:
1. User asks question → Streamlit UI
2. classify_query() → Determines 'knowledge_retrieval'
3. route_query() → Routes to llamaindex_node
4. llamaindex_node() → Calls process_knowledge_query()
5. process_knowledge_query() → Uses create_knowledge_engine()
6. create_knowledge_engine() → Returns _ENGINE_CACHE or creates new
   
ENGINE CREATION (First Time):
1. SimpleDirectoryReader reads from data/documents/
2. VectorStoreIndex.from_documents() creates in-memory index
3. Embeddings generated using OpenAI text-embedding-3-small
4. RouterQueryEngine created with Vector + SQL tools
5. Engine cached in _ENGINE_CACHE global variable

QUERY EXECUTION:
1. RouterQueryEngine.query(question)
2. LLMSingleSelector chooses Vector or SQL engine
3. Vector engine searches documents by semantic similarity
4. Returns top 3 most relevant chunks
5. LLM synthesizes answer from chunks
""")

# 6. Upload implications
print("\n### 6. DOCUMENT UPLOAD IMPLICATIONS ###")
print("-" * 80)
print("""
CURRENT STATE (Option A):
✅ Upload button exists in UI
❌ Files NOT saved to disk
❌ Index NOT updated with new documents
❌ New documents NOT searchable

TO MAKE UPLOAD WORK (Option B):
1. Save file to data/documents/ directory
2. Clear _ENGINE_CACHE to force rebuild
3. Next query will trigger create_knowledge_engine()
4. SimpleDirectoryReader will include new document
5. New VectorStoreIndex created with all documents

ALTERNATIVE (Incremental):
1. Save file to data/documents/
2. Load new document with SimpleDirectoryReader
3. Use VectorStoreIndex.insert() to add to existing index
4. Update _ENGINE_CACHE with modified index
5. Immediate availability without full rebuild

CHALLENGE:
- LlamaIndex creates in-memory index (not persistent)
- Full rebuild on every app restart
- ChromaDB is only used by LangChain, not LlamaIndex
""")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
