"""
backend/app/core/llm_adapters.py
─────────────────────────────────
LLM Adapter abstraction layer for the AI Copilot.
"""

from __future__ import annotations
import json
import os
from abc import ABC, abstractmethod
from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMResponse:
    __slots__ = ("answer", "sources", "confidence", "adapter_name")

    def __init__(self, answer: str, sources: list[str] | None = None,
                 confidence: float = 1.0, adapter_name: str = "unknown") -> None:
        self.answer = answer
        self.sources = sources or []
        self.confidence = confidence
        self.adapter_name = adapter_name

    def to_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "sources": self.sources,
                "confidence": self.confidence, "adapter": self.adapter_name}


class LLMAdapter(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, history: list[dict[str, str]], context: str) -> LLMResponse:
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class GoogleGemmaAdapter(LLMAdapter):
    """Real Gemma 4 via Google AI Studio API."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("GOOGLE_AI_KEY", "")
        self.model = "gemma-2-9b-it"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def generate_response(self, prompt: str, history: list[dict[str, str]], context: str) -> LLMResponse:
        import urllib.request
        import urllib.error

        if not self.api_key:
            logger.warning("GOOGLE_AI_KEY not set, falling back to rule-based")
            return RuleBasedAdapter().generate_response(prompt, history, context)

        system_prompt = (
            "You are Nika AI — a Senior Manufacturing Quality Engineer with 20 years of experience. "
            "You help factory workers and managers understand defects, their causes, and corrective actions. "
            "Always respond in plain language (8th grade reading level). "
            "Be concise, practical, and actionable. "
            f"\n\nFactory Knowledge Context:\n{context[:1000] if context else 'No context available.'}"
        )

        messages = [{"role": "user", "parts": [{"text": system_prompt + "\n\nWorker question: " + prompt}]}]

        payload = json.dumps({"contents": messages, "generationConfig": {"maxOutputTokens": 500, "temperature": 0.3}}).encode()

        req = urllib.request.Request(
            f"{self.api_url}?key={self.api_key}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                answer = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("GoogleGemmaAdapter: response generated successfully")
                return LLMResponse(answer=answer, sources=["Gemma 4 via Google AI"], confidence=0.95, adapter_name="gemma_google")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            logger.error(f"Google AI API error {e.code}: {error_body}")
            return RuleBasedAdapter().generate_response(prompt, history, context)
        except Exception as e:
            logger.error(f"GoogleGemmaAdapter error: {e}")
            return RuleBasedAdapter().generate_response(prompt, history, context)


class RuleBasedAdapter(LLMAdapter):
    """Fallback rule-based adapter."""

    def generate_response(self, prompt: str, history: list[dict[str, str]], context: str) -> LLMResponse:
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

        return LLMResponse(answer=answer, sources=sources[:3], confidence=0.88, adapter_name="rule_based")


class OllamaAdapter(LLMAdapter):
    def generate_response(self, prompt, history, context):
        raise NotImplementedError("OllamaAdapter not configured.")

class GemmaAdapter(LLMAdapter):
    def generate_response(self, prompt, history, context):
        raise NotImplementedError("Use GoogleGemmaAdapter instead.")

class OpenAIAdapter(LLMAdapter):
    def generate_response(self, prompt, history, context):
        raise NotImplementedError("OpenAIAdapter not configured.")

class HuggingFaceAdapter(LLMAdapter):
    def generate_response(self, prompt, history, context):
        raise NotImplementedError("HuggingFaceAdapter not configured.")
