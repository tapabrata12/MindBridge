from pathlib import Path
from src.core.config import settings
import chromadb
CHROMA_DIR = Path(settings.CHROMA_DIR)
collection_name = settings.CHROMA_COLLECTION_NAME