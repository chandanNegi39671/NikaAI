"""
backend/app/core/knowledge_providers.py
────────────────────────────────────────
Knowledge retrieval abstraction for the AI Copilot RAG pipeline.

Architecture:
  The Copilot service never calls SQL or vector store directly.
  It depends only on KnowledgeProvider, enabling future swap from
  keyword-based retrieval to semantic vector search without changing
  any service or endpoint code.

Lifecycle:
  Sprint 8 → KeywordKnowledgeProvider (SQL LIKE search, zero deps)
  Sprint 9+ → VectorKnowledgeProvider (pgvector / Chroma / Weaviate)

Extension point:
  To add a new retrieval backend:
    1. Subclass KnowledgeProvider.
    2. Implement retrieve_context().
    3. Add a branch in provider_factory.get_knowledge_provider().
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeProvider(ABC):
    """Abstract base class for knowledge retrieval backends.

    retrieve_context() returns a formatted string suitable for injection
    into an LLM prompt as grounding context.
    """

    @abstractmethod
    def retrieve_context(self, query: str, db: Session) -> str:
        """Retrieve and format knowledge documents relevant to the query.

        Args:
            query: The user's question or topic.
            db:    Active SQLAlchemy session (for DB-backed providers).

        Returns:
            Formatted string block for prompt injection.
            Each document entry is separated by newlines.
        """
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class KeywordKnowledgeProvider(KnowledgeProvider):
    """Keyword-based knowledge retrieval using SQL LIKE matching.

    Searches KnowledgeDocument.title, content, and tags.
    Also enriches context with FactoryMemory entries matching the query.

    This is the Sprint 8 default — honest, deterministic, zero external deps.
    A clear extension point is left for VectorKnowledgeProvider.
    """

    def retrieve_context(self, query: str, db: Session) -> str:
        from app.core.repository import factory_memory_repo, knowledge_document_repo

        context_parts: list[str] = []

        # 1. Search knowledge documents
        docs = knowledge_document_repo.search_by_keyword(db, query=query, limit=5)
        if docs:
            context_parts.append("=== Knowledge Base Documents ===")
            for doc in docs:
                context_parts.append(
                    f"📄 {doc.title} [{doc.doc_type.upper()}]:\n{doc.content[:400].strip()}"
                )

        # 2. Enrich with factory memory entries
        memories = factory_memory_repo.get_multi(db, limit=3)
        relevant_memories = [
            m
            for m in memories
            if query.lower() in (m.defect_class or "").lower()
            or query.lower() in (m.description or "").lower()
        ]
        if relevant_memories:
            context_parts.append("\n=== Factory Memory (Defect Patterns) ===")
            for m in relevant_memories[:2]:
                context_parts.append(
                    f"• {m.defect_class}: {m.description or ''}\n"
                    f"  Pattern: {m.recurring_defect_pattern or 'N/A'}\n"
                    f"  Action: {m.recommended_action or 'N/A'}"
                )

        if not context_parts:
            context_parts.append(
                "No specific documents found for this query. "
                "Responding based on general factory quality standards."
            )

        result = "\n".join(context_parts)
        logger.debug(
            f"KeywordKnowledgeProvider retrieved {len(docs)} docs + "
            f"{len(relevant_memories)} memories for query: '{query[:60]}'"
        )
        return result


class VectorKnowledgeProvider(KnowledgeProvider):
    """Semantic vector-based retrieval provider.

    Extension point for Sprint 9+.
    Requires a vector store (pgvector, Chroma, or Weaviate) and an
    embedding model (sentence-transformers, OpenAI embeddings, etc.).

    Set KNOWLEDGE_PROVIDER=vector in settings and implement this class.
    """

    def retrieve_context(self, query: str, db: Session) -> str:
        # Extension point: Sprint 9 will implement embedding generation
        # and cosine similarity search against the vector store.
        raise NotImplementedError(
            "VectorKnowledgeProvider is not yet implemented. "
            "Configure a vector store and set KNOWLEDGE_PROVIDER=vector."
        )
