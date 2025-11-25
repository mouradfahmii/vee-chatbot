from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from app.config import settings
import chromadb
from chromadb.api import Collection
from chromadb.utils import embedding_functions


@dataclass
class Document:
    doc_id: str
    content: str
    metadata: dict


class VectorStore:
    """Thin wrapper around Chroma for persistence + retrieval."""

    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=str(settings.chroma_path))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        self.collection: Collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=embedding_fn,
        )

    def reset(self) -> None:
        self.client.delete_collection(settings.collection_name)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            embedding_function=embedding_fn,
        )

    def add(self, documents: Sequence[Document]) -> None:
        if not documents:
            return
        self.collection.add(
            ids=[doc.doc_id for doc in documents],
            documents=[doc.content for doc in documents],
            metadatas=[doc.metadata for doc in documents],
        )

    def query(self, text: str, n_results: int | None = None) -> List[Document]:
        limit = n_results or settings.max_context_documents
        results = self.collection.query(query_texts=[text], n_results=limit)
        docs: List[Document] = []
        for doc_id, content, metadata in zip(
            results.get("ids", [[]])[0],
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
        ):
            docs.append(Document(doc_id=doc_id, content=content, metadata=metadata))
        return docs


vector_store = VectorStore()
