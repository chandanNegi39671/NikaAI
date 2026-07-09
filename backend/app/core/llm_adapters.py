"""
backend/app/core/llm_adapters.py
─────────────────────────────────
LLM Adapter abstraction layer for the AI Copilot.

Architecture:
  The Copilot service never calls a concrete LLM implementation directly.
  It depends only on LLMAdapter, allowing swapping of backends without
  modifying any service or endpoint code.

  Active adapter is selected at runtime by ProviderFactory based on the
  LLM_PROVIDER configuration value.

Lifecycle:
  Sprint 8 → RuleBasedAdapter (deterministic, zero external dependencies)
  Sprint 9 → OllamaAdapter (local GPU, AMD ROCm compatible)
  Sprint 10 → OpenAI / GemmaAdapter (cloud inference)

Extension point:
  To add a new LLM backend:
    1. Subclass LLMAdapter.
    2. Implement generate_response().
    3. Add a branch in provider_factory.get_llm_adapter().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Response dataclass ────────────────────────────────────────────────────────


class LLMResponse:
    """Normalized response object returned by every LLMAdapter."""

    __slots__ = ("answer", "sources", "confidence", "adapter_name")

    def __init__(
        self,
        answer: str,
        sources: list[str] | None = None,
        confidence: float = 1.0,
        adapter_name: str = "unknown",
    ) -> None:
        self.answer = answer
        self.sources = sources or []
        self.confidence = confidence
        self.adapter_name = adapter_name

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "adapter": self.adapter_name,
        }


# ── Abstract base ─────────────────────────────────────────────────────────────


class LLMAdapter(ABC):
    """Abstract base class for all LLM backend adapters.

    Every concrete adapter must implement generate_response().
    history is a list of dicts with keys: role ('user'|'assistant') and content.
    context is a string block of retrieved knowledge/factory memory to ground responses.
    """

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        """Generate a grounded response to the given prompt.

        Args:
            prompt:  The latest user message.
            history: Previous turns (oldest first). Each dict has 'role' and 'content'.
            context: Retrieved knowledge documents and factory analytics.

        Returns:
            LLMResponse with answer text, sources, and confidence.
        """
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ── RuleBasedAdapter (Sprint 8 default) ────────────────────────────────────────


class RuleBasedAdapter(LLMAdapter):
    """Deterministic rule-based response generation.

    Uses keyword pattern matching against the provided context string.
    Produces grounded answers citing factory memory and knowledge documents.
    No external dependencies, no network calls, always available.
    """

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        lower = prompt.lower()
        sources: list[str] = []

        # Extract knowledge document titles mentioned in context for citations
        for line in context.splitlines():
            if line.startswith("📄"):
                title = line.replace("📄", "").split(":")[0].strip()
                if title:
                    sources.append(title)

        # Defect-type responses grounded on context
        if any(k in lower for k in ("crack", "fracture", "break")):
            answer = (
                "⚠️ Surface crack detected in inspection data.\n\n"
                "Based on factory knowledge:\n"
                "• Immediately stop CNC operation and quarantine the part.\n"
                "• Root causes: thermal load, stress concentration, micro-voids in raw stock.\n"
                "• Check coolant flow rate and pre-heating compliance.\n"
                "• Document in CAPA system before resuming production.\n\n"
                + self._extract_sop_excerpt(context, "crack")
            )
        elif any(k in lower for k in ("scratch", "abrasion", "scuff")):
            answer = (
                "⚠️ Surface scratch detected.\n\n"
                "Recommended SOP:\n"
                "• Wipe guide rails and re-align conveyor belts.\n"
                "• If depth < 0.2mm: buff and re-inspect.\n"
                "• If depth ≥ 0.2mm: escalate to supervisor and scrap part.\n"
                "• Install protective rubber sleeves on grippers.\n\n"
                + self._extract_sop_excerpt(context, "scratch")
            )
        elif any(k in lower for k in ("dent", "deformation", "indent")):
            answer = (
                "⚠️ Dent / deformation detected.\n\n"
                "Recommended action:\n"
                "• Check ejector pin pressure and hydraulic valve seals.\n"
                "• Recalibrate ejector stroke limiters.\n"
                "• Scrap part if structural integrity is compromised.\n\n"
                + self._extract_sop_excerpt(context, "dent")
            )
        elif any(k in lower for k in ("model", "version", "weight", "checkpoint")):
            answer = (
                "🤖 Model Registry Status:\n\n"
                "The production model is managed through the Model Registry. "
                "Visit the Registry page to view mAP, precision, recall, and deployment lifecycle status.\n"
                "Use the 'Switch Model' action to hot-swap weights without restarting the server.\n\n"
                + self._extract_context_summary(context)
            )
        elif any(k in lower for k in ("audit", "log", "compliance", "history")):
            answer = (
                "📋 Audit & Compliance:\n\n"
                "All operator actions are logged with timestamp, IP address, and entity changes.\n"
                "Access the Audit Logs page to filter by date, user, action type, or request ID.\n\n"
                + self._extract_context_summary(context)
            )
        elif any(k in lower for k in ("machine", "failure", "breakdown")):
            answer = (
                "🔧 Machine Health Context:\n\n"
                + self._extract_context_summary(context)
                + "\n\nRefer to Maintenance Intelligence for predictive health scores and RUL estimates."
            )
        else:
            answer = (
                "Hello. I am the Nika AI Quality Copilot — your factory intelligence assistant.\n\n"
                "I can help you with:\n"
                "• Defect diagnosis and SOP lookup\n"
                "• Model registry and deployment status\n"
                "• Inspection history and analytics\n"
                "• Compliance and audit trail queries\n\n"
                "How can I assist you on the production line today?"
            )

        logger.info(
            f"RuleBasedAdapter generated response for prompt: '{prompt[:60]}...'"
        )
        return LLMResponse(
            answer=answer,
            sources=sources[:3],
            confidence=0.88,
            adapter_name="rule_based",
        )

    def _extract_sop_excerpt(self, context: str, keyword: str) -> str:
        """Pull the first matching SOP excerpt from the context string."""
        lines = context.splitlines()
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                excerpt = "\n".join(lines[i : i + 3]).strip()
                if excerpt:
                    return f"\n📖 From knowledge base:\n{excerpt}"
        return ""

    def _extract_context_summary(self, context: str) -> str:
        """Return the first 300 characters of the context block."""
        if not context:
            return ""
        return context[:300].strip() + ("..." if len(context) > 300 else "")


# ── Placeholder adapters (Sprint 9+ extension points) ─────────────────────────


class OllamaAdapter(LLMAdapter):
    """Adapter for local Ollama inference server (AMD ROCm compatible).

    Extension point for Sprint 9.
    Set LLM_PROVIDER=ollama and configure OLLAMA_BASE_URL in settings.
    """

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        # Extension point: Sprint 9 will implement real HTTP call to Ollama API
        raise NotImplementedError(
            "OllamaAdapter is not yet configured. "
            "Set OLLAMA_BASE_URL in settings and implement the HTTP client."
        )


class GemmaAdapter(LLMAdapter):
    """Adapter for Gemma LLM server endpoint.

    Extension point for Sprint 9.
    Set LLM_PROVIDER=gemma and configure GEMMA_API_URL in settings.
    """

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        raise NotImplementedError(
            "GemmaAdapter is not yet configured. "
            "Set GEMMA_API_URL in settings and implement the HTTP client."
        )


class OpenAIAdapter(LLMAdapter):
    """Adapter for OpenAI-compatible APIs (GPT-4, Azure OpenAI, etc).

    Extension point for Sprint 10.
    Set LLM_PROVIDER=openai and configure OPENAI_API_KEY in settings.
    """

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        raise NotImplementedError(
            "OpenAIAdapter is not yet configured. "
            "Set OPENAI_API_KEY in settings and implement the HTTP client."
        )


class HuggingFaceAdapter(LLMAdapter):
    """Adapter for HuggingFace Inference API endpoints.

    Extension point for Sprint 10.
    Set LLM_PROVIDER=huggingface and configure HF_API_KEY in settings.
    """

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        raise NotImplementedError(
            "HuggingFaceAdapter is not yet configured. "
            "Set HF_API_KEY in settings and implement the HTTP client."
        )
