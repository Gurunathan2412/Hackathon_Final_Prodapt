# Configuration settings
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / '.env'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL_CLASSIFY = os.getenv('OPENAI_MODEL_CLASSIFY', 'gpt-4o-mini')
OPENAI_MODEL_AGENTS = os.getenv('OPENAI_MODEL_AGENTS', 'gpt-4o-mini')
OPENAI_EMBED_MODEL = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
CHROMA_DIR = str(PROJECT_ROOT / 'data' / 'chromadb')
DOCUMENTS_DIR = str(PROJECT_ROOT / 'data' / 'documents')
SQLITE_DB_PATH = str(PROJECT_ROOT / 'data' / 'telecom.db')

DEFAULT_CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '800'))
DEFAULT_CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))

# Flags
ENABLE_LLM_CLASSIFICATION = os.getenv('ENABLE_LLM_CLASSIFICATION', 'false').lower() == 'true'

LOG_LEVEL = os.getenv('LOG_LEVEL','INFO')
