from src.rag.chroma_client import (
    get_chroma_client,
    get_knowledge_collection,
)


def test_chroma_client_created():
    client = get_chroma_client()

    assert client is not None


def test_collection_created():
    collection = get_knowledge_collection()

    assert collection is not None
    assert collection.name is not None


def test_collection_count():
    collection = get_knowledge_collection()

    assert isinstance(collection.count(), int)