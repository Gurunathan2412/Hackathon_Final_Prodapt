import os
from typing import List
from config.config import DOCUMENTS_DIR, CHROMA_DIR, OPENAI_EMBED_MODEL

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
    from langchain_community.vectorstores import Chroma  # type: ignore
    from langchain_community.document_loaders import TextLoader  # type: ignore
    from langchain_openai import OpenAIEmbeddings  # type: ignore
except Exception:  # pragma: no cover
    RecursiveCharacterTextSplitter = Chroma = TextLoader = OpenAIEmbeddings = object  # type: ignore


def load_raw_documents() -> List[str]:
    docs = []
    for fname in os.listdir(DOCUMENTS_DIR):
        path = os.path.join(DOCUMENTS_DIR, fname)
        if os.path.isfile(path) and fname.lower().endswith(('.txt', '.md')):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    docs.append(f.read())
            except Exception:
                continue
    return docs


def build_vector_store(persist: bool = True):
    if Chroma is object:
        return None
    texts = load_raw_documents()
    if not texts:
        return None
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = []
    for t in texts:
        chunks.extend(splitter.split_text(t))
    embeddings = OpenAIEmbeddings(model=OPENAI_EMBED_MODEL) if OpenAIEmbeddings is not object else None
    if not embeddings:
        return None
    vs = Chroma.from_texts(chunks, embedding=embeddings, persist_directory=CHROMA_DIR if persist else None)
    if persist:
        vs.persist()
    return vs

_vector_store_cached = None


def ensure_vector_store():
    global _vector_store_cached
    if _vector_store_cached is None:
        _vector_store_cached = build_vector_store(persist=True)
    return _vector_store_cached