from pathlib import Path
from src.core.config import settings
import chromadb
CHROMA_DIR = Path(settings.CHROMA_DIR)
COLLECTION = settings.CHROMA_COLLECTION_NAME

def get_chroma_client():
    """
    This method for creating / opening the connection
    Step 1: get / create the dir
    Step 2: opens the ChromaDB database at the folder dir path we defined
    :return: chromadb.PersistentClient
    """
    CHROMA_DIR.mkdir(exist_ok=True, parents=True)

    return chromadb.PersistentClient(path=str(CHROMA_DIR))

def get_knowledge_collection():
    """
    Step 1: Open the connection
    Step 2: Create / get the knowledge collection
    """
    client = get_chroma_client()

    return client.get_or_create_collection(name=COLLECTION)