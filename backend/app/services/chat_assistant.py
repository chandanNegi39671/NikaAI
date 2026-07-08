"""
backend/app/services/chat_assistant.py
──────────────────────────────────────
Upgraded AI Chat Assistant service using normalized database conversation logs,
RAG pipeline keyword lookup, and the configuration-driven adapter abstractions.
"""

from sqlalchemy.orm import Session
from app.core.logging import get_logger
from app.core.provider_factory import get_llm_adapter, get_knowledge_provider
from app.core.repository import conversation_repo, conversation_message_repo

logger = get_logger(__name__)

def ask_factory_assistant(db: Session, question: str, session_key: str | None = None) -> dict:
    """Resolve assistant query using conversation history, RAG context, and configuration-driven LLM.

    If session_key is provided, conversation history is preserved and appended to the DB.
    If session_key is absent, a local transient context is used.
    """
    logger.info(f"AI Assistant Query (Session: {session_key}): '{question}'")
    
    # 1. Fetch or create conversation session
    conversation_id = None
    history_list = []
    
    if session_key:
        conv = conversation_repo.get_or_create(db, session_key)
        conversation_id = conv.id
        # Load last 10 messages for context window stability
        db_messages = conversation_message_repo.get_messages_for_conversation(db, conv.id, limit=10)
        for msg in db_messages:
            history_list.append({
                "role": msg.role,
                "content": msg.content
            })
            
    # 2. Retrieve knowledge context via the configured provider
    knowledge_provider = get_knowledge_provider()
    context_str = knowledge_provider.retrieve_context(question, db)
    
    # 3. Request completion from configured LLM adapter
    llm_adapter = get_llm_adapter()
    llm_response = llm_adapter.generate_response(question, history_list, context_str)
    
    # 4. Log conversation history in database
    if conversation_id:
        # Save user message
        conversation_message_repo.add_message(db, conversation_id, "user", question)
        # Save assistant message
        conversation_message_repo.add_message(db, conversation_id, "assistant", llm_response.answer)
        
    return {
        "question": question,
        "answer": llm_response.answer,
        "sources": llm_response.sources,
        "adapter": llm_response.adapter_name,
        "confidence": llm_response.confidence
    }

def get_session_history(db: Session, session_key: str) -> list[dict]:
    """Retrieve message history for a given conversation key."""
    conv = conversation_repo.get_by_session_key(db, session_key)
    if not conv:
        return []
    messages = conversation_message_repo.get_messages_for_conversation(db, conv.id)
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
        }
        for msg in messages
    ]

def clear_session_history(db: Session, session_key: str) -> bool:
    """Clear message history for a given conversation key."""
    conv = conversation_repo.get_by_session_key(db, session_key)
    if not conv:
        return False
    conversation_message_repo.delete_for_conversation(db, conv.id)
    return True
