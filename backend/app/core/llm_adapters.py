"""
backend/app/core/llm_adapters.py
─────────────────────────────────
LLM Adapter abstraction layer for the AI Copilot.

Architecture:
  LLMAdapter (ABC)
    ├── GoogleGeminiAdapter  — Google AI Studio REST API (Gemini / Gemma models)
    ├── RuleBasedAdapter     — deterministic keyword rules, zero external deps
    ├── OllamaAdapter        — local Ollama server (stub, Sprint 9+)
    ├── OpenAIAdapter        — OpenAI-compatible API (stub, Sprint 9+)
    └── HuggingFaceAdapter   — HuggingFace Inference API (stub, Sprint 9+)

Configuration (via Settings / .env):
  GOOGLE_AI_KEY=<your-api-key>          ← enables GoogleGeminiAdapter
  GOOGLE_AI_MODEL=gemini-2.0-flash-lite ← model to use (default)

Model options for GOOGLE_AI_MODEL:
  gemini-2.0-flash-lite   — fast, free tier, recommended
  gemini-1.5-flash-latest — more capable
  gemma-2-9b-it           — open Gemma model (may need AI Studio allowlist)

Get a free Google AI Studio key at: https://aistudio.google.com/app/apikey
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Value object
# ─────────────────────────────────────────────────────────────────────────────


class LLMResponse:
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


# ─────────────────────────────────────────────────────────────────────────────
# Abstract base
# ─────────────────────────────────────────────────────────────────────────────


class LLMAdapter(ABC):
    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ─────────────────────────────────────────────────────────────────────────────
# Google AI Studio adapter  (Gemini / Gemma via generativelanguage API)
# ─────────────────────────────────────────────────────────────────────────────


class GoogleGeminiAdapter(LLMAdapter):
    """Calls Google AI Studio's generateContent REST endpoint.

    Supports both Gemini and Gemma models.  The model is configurable via
    settings.google_ai_model (env var GOOGLE_AI_MODEL).

    Fallback: on any error, delegates to RuleBasedAdapter so the assistant
    is always available even when the API is unreachable.
    """

    def __init__(self) -> None:
        # Import here to avoid a circular import at module load time
        from app.core.config import settings

        self._api_key: str = settings.google_ai_key
        self._model: str = settings.google_ai_model
        self._api_url: str = (
            "https://generativelanguage.googleapis.com/v1beta"
            f"/models/{self._model}:generateContent"
        )

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        import urllib.error
        import urllib.request

        if not self._api_key:
            logger.warning(
                "GoogleGeminiAdapter: GOOGLE_AI_KEY not configured — "
                "falling back to RuleBasedAdapter"
            )
            return RuleBasedAdapter().generate_response(prompt, history, context)

        system_prompt = (
            "You are Nika AI — a Senior Manufacturing Quality Engineer with "
            "20 years of experience. "
            "You help factory workers and managers understand defects, their "
            "causes, and corrective actions. "
            "Always respond in plain language (8th-grade reading level). "
            "Be concise, practical, and actionable.\n\n"
            f"Factory Knowledge Context:\n"
            f"{context[:1500].strip() if context else 'No context available.'}"
        )

        # Build the conversation in Gemini multi-turn format
        contents: list[dict] = []

        # Prepend system context as a user/model exchange so the model adopts
        # the persona even when the API doesn't have a dedicated system field
        # (Gemini API v1beta does support systemInstruction, but the
        #  generateContent endpoint works without it too).
        for msg in history[-10:]:  # cap context window to last 10 turns
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Final user turn with full system prompt prepended
        user_text = f"{system_prompt}\n\nWorker question: {prompt}"
        contents.append({"role": "user", "parts": [{"text": user_text}]})

        payload = json.dumps(
            {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": 600,
                    "temperature": 0.3,
                    "topP": 0.9,
                },
                "safetySettings": [
                    # Relax safety thresholds for industrial / manufacturing topics
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
                ],
            }
        ).encode()

        req = urllib.request.Request(
            f"{self._api_url}?key={self._api_key}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            # Navigate the Gemini response structure
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning(
                    "GoogleGeminiAdapter: empty candidates in response",
                    extra={"model": self._model},
                )
                return RuleBasedAdapter().generate_response(prompt, history, context)

            answer = (
                candidates[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )

            if not answer:
                logger.warning("GoogleGeminiAdapter: blank answer text in response")
                return RuleBasedAdapter().generate_response(prompt, history, context)

            logger.info(
                "GoogleGeminiAdapter: response generated",
                extra={"model": self._model, "chars": len(answer)},
            )
            return LLMResponse(
                answer=answer,
                sources=[f"Google AI ({self._model})"],
                confidence=0.95,
                adapter_name="google_gemini",
            )

        except urllib.error.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.read().decode()
            except Exception:
                pass
            logger.error(
                "GoogleGeminiAdapter: HTTP error",
                extra={"status": exc.code, "body": error_body[:300], "model": self._model},
            )
            return RuleBasedAdapter().generate_response(prompt, history, context)

        except urllib.error.URLError as exc:
            logger.error(
                "GoogleGeminiAdapter: network error",
                extra={"reason": str(exc.reason), "model": self._model},
            )
            return RuleBasedAdapter().generate_response(prompt, history, context)

        except Exception as exc:
            logger.error(
                "GoogleGeminiAdapter: unexpected error",
                extra={"error": str(exc), "model": self._model},
            )
            return RuleBasedAdapter().generate_response(prompt, history, context)


# ─────────────────────────────────────────────────────────────────────────────
# Backward-compatible alias so existing imports don't break
# ─────────────────────────────────────────────────────────────────────────────

#: Alias kept for backward compatibility with any code that imported the old name.
GoogleGemmaAdapter = GoogleGeminiAdapter


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based fallback (zero external deps)
# ─────────────────────────────────────────────────────────────────────────────


class RuleBasedAdapter(LLMAdapter):
    """Deterministic keyword-matching adapter.

    Always available — used as fallback when no LLM API key is configured or
    when any upstream API call fails.
    """

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, str]],
        context: str,
    ) -> LLMResponse:
        lower = prompt.lower()
        sources: list[str] = []

        for line in context.splitlines():
            if line.startswith("📄"):
                title = line.replace("📄", "").split(":")[0].strip()
                if title:
                    sources.append(title)

        if any(k in lower for k in ("crack", "fracture", "break")):
            answer = (
                "⚠️ Surface crack detected.\n\n"
                "• Immediately stop CNC operation and quarantine the part.\n"
                "• Root causes: thermal load, stress concentration, micro-voids.\n"
                "• Check coolant flow rate and pre-heating compliance.\n"
                "• Document in CAPA system before resuming production."
            )
        elif any(k in lower for k in ("scratch", "abrasion", "scuff")):
            answer = (
                "⚠️ Surface scratch detected.\n\n"
                "• If depth < 0.2mm: buff and re-inspect.\n"
                "• If depth ≥ 0.2mm: escalate to supervisor and scrap part.\n"
                "• Install protective rubber sleeves on grippers."
            )
        elif any(k in lower for k in ("dent", "deformation")):
            answer = (
                "⚠️ Dent/deformation detected.\n\n"
                "• Check ejector pin pressure and hydraulic valve seals.\n"
                "• Scrap part if structural integrity is compromised."
            )
        else:
            answer = (
                "Hello! I am Nika AI Quality Copilot.\n\n"
                "I can help with:\n"
                "• Defect diagnosis and corrective actions\n"
                "• Inspection history and analytics\n"
                "• Machine maintenance guidance\n\n"
                "What quality issue can I help you with today?"
            )

        return LLMResponse(
            answer=answer,
            sources=sources[:3],
            confidence=0.88,
            adapter_name="rule_based",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Stub adapters (Sprint 9+ extension points)
# ─────────────────────────────────────────────────────────────────────────────


class OllamaAdapter(LLMAdapter):
    """Local Ollama LLM server adapter — Sprint 9+ implementation."""

    def generate_response(
        self, prompt: str, history: list[dict[str, str]], context: str
    ) -> LLMResponse:
        raise NotImplementedError(
            "OllamaAdapter is not yet implemented. "
            "Start Ollama locally and implement this class in Sprint 9."
        )


class OpenAIAdapter(LLMAdapter):
    """OpenAI-compatible API adapter — Sprint 9+ implementation."""

    def generate_response(
        self, prompt: str, history: list[dict[str, str]], context: str
    ) -> LLMResponse:
        raise NotImplementedError(
            "OpenAIAdapter is not yet implemented. "
            "Set OPENAI_API_KEY and implement this class in Sprint 9."
        )


class HuggingFaceAdapter(LLMAdapter):
    """HuggingFace Inference API adapter — Sprint 9+ implementation."""

    def generate_response(
        self, prompt: str, history: list[dict[str, str]], context: str
    ) -> LLMResponse:
        raise NotImplementedError(
            "HuggingFaceAdapter is not yet implemented. "
            "Set HF_API_KEY and implement this class in Sprint 9."
        )


# Kept for any legacy imports
class GemmaAdapter(LLMAdapter):
    """Deprecated — use GoogleGeminiAdapter instead."""

    def generate_response(
        self, prompt: str, history: list[dict[str, str]], context: str
    ) -> LLMResponse:
        raise NotImplementedError(
            "GemmaAdapter is deprecated. Use GoogleGeminiAdapter (via provider_factory)."
        )
