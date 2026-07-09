"""
backend/app/api/endpoints/assistant.py
───────────────────────────────────────
Endpoints for AI Chat Assistant Q&A interface and Knowledge Base documents.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.core.repository import knowledge_document_repo
from app.models.db_models import KnowledgeDocument
from app.services.chat_assistant import (
    ask_factory_assistant,
    clear_session_history,
    get_session_history,
)

router = APIRouter(
    prefix="/api/v1/assistant",
    tags=["AI Assistant"],
    dependencies=[Depends(PermissionChecker("inspection:read"))],
)

# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class AssistantQuery(BaseModel):
    question: str
    session_key: Optional[str] = Field(
        None, description="Persisted chat session key for loading history context"
    )


class AssistantResponse(BaseModel):
    question: str
    answer: str
    sources: List[str]
    adapter: str
    confidence: float


class MessageHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    timestamp: Optional[str] = None


class KnowledgeDocCreateRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document body manual details")
    doc_type: str = Field(
        "manual", description="doc_type: manual | sop | faq | maintenance"
    )
    tags: Optional[str] = Field(None, description="Comma-separated tag items")


class KnowledgeDocResponse(BaseModel):
    id: str
    title: str
    content: str
    doc_type: str
    tags: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/ask", response_model=AssistantResponse, summary="Ask Factory AI Assistant"
)
def ask_assistant(query: AssistantQuery, db: Session = Depends(get_db)):
    """Ask AI Copilot questions about defect calibration, manual SOP details, or history statistics."""
    if not query.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty."
        )
    res = ask_factory_assistant(db, query.question, query.session_key)
    return res


@router.get(
    "/history/{session_key}",
    response_model=List[MessageHistoryItem],
    summary="Get chat session history list",
)
def get_assistant_history(session_key: str, db: Session = Depends(get_db)):
    """Load conversation history messages for a specific session key."""
    return get_session_history(db, session_key)


@router.delete("/history/{session_key}", summary="Clear chat session history")
def clear_assistant_history(session_key: str, db: Session = Depends(get_db)):
    """Wipe out saved message log items for a specific conversation session key."""
    success = clear_session_history(db, session_key)
    return {"success": success, "detail": "History messages deleted."}


# ── Knowledge Base CRUD (Additive Only) ───────────────────────────────────────


@router.post(
    "/knowledge",
    response_model=KnowledgeDocResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge base manual",
    dependencies=[Depends(PermissionChecker("admin"))],
)
def create_knowledge_document(
    req: KnowledgeDocCreateRequest, db: Session = Depends(get_db)
):
    """Add a new SOP, FAQ, or training guide to the Copilot's RAG knowledge database."""
    new_doc = KnowledgeDocument(
        title=req.title,
        content=req.content,
        doc_type=req.doc_type,
        tags=req.tags,
        is_active=True,
    )
    knowledge_document_repo.create(db, new_doc)
    return new_doc


@router.get(
    "/knowledge",
    response_model=List[KnowledgeDocResponse],
    summary="List active knowledge base documents",
)
def list_knowledge_documents(
    doc_type: Optional[str] = None, db: Session = Depends(get_db)
):
    """Fetch active documents filterable by doc_type."""
    return knowledge_document_repo.list_active(db, doc_type=doc_type)


@router.get(
    "/knowledge/search",
    response_model=List[KnowledgeDocResponse],
    summary="Keyword search knowledge documents",
)
def search_knowledge_documents(
    query: str, doc_type: Optional[str] = None, db: Session = Depends(get_db)
):
    """Full-text search knowledge base entries using keyword queries."""
    if not query.strip():
        return []
    return knowledge_document_repo.search_by_keyword(db, query=query, doc_type=doc_type)
