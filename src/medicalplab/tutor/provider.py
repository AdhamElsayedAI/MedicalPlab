"""Provider-agnostic interface and adapter implementations for Grounded Generative Tutor."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProviderResponse(BaseModel):
    raw_text: str
    structured_data: dict[str, Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    ttft_ms: float | None = None
    model: str = ""  # ACTUAL model that produced this response (post-failover, if any)
    provider: str = ""
    requested_model: str = ""  # Originally configured/requested model, before any failover
    provider_failover_applied: bool = False
    primary_provider_error: str | None = None  # Error from the requested/primary model attempt, if it failed


@runtime_checkable
class GenerativeProvider(Protocol):
    provider_name: str
    model_name: str

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> ProviderResponse:
        ...


class StubGenerativeProvider:
    """Deterministic, offline generative provider for unit testing, CI, and stub evaluation."""

    def __init__(self, model_name: str = "stub-tutor-v1") -> None:
        self.provider_name = "stub"
        self.model_name = model_name
        self._custom_responses: dict[str, dict[str, Any]] = {}

    def set_custom_response(self, query_substr: str, structured_dict: dict[str, Any]) -> None:
        self._custom_responses[query_substr.lower()] = structured_dict

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> ProviderResponse:
        start_t = time.perf_counter()
        lowered_user = user_prompt.lower()

        # Check if custom response registered
        for substr, custom in self._custom_responses.items():
            if substr in lowered_user:
                latency = (time.perf_counter() - start_t) * 1000.0
                return ProviderResponse(
                    raw_text=json.dumps(custom),
                    structured_data=custom,
                    input_tokens=120,
                    output_tokens=150,
                    latency_ms=round(latency, 2),
                    model=self.model_name,
                    provider=self.provider_name,
                    requested_model=self.model_name,
                )

        # Default Socratic responses based on topic / mode
        is_pre = "<state>pre_submission</state>" in lowered_user

        # Case 1: RAAS mechanisms
        if "substrate" in lowered_user or "renin" in lowered_user or "angiotensinogen" in lowered_user or "raas" in lowered_user:
            default_data = {
                "message": (
                    "In the renin-angiotensin system, renin is an active proteolytic enzyme. "
                    "Active renin acts upon its substrate to generate angiotensin I."
                ),
                "socratic_question": "What substrate does active renin act upon to generate angiotensin I?",
                "hints": [
                    "Level 1: Recall that active renin is an active proteolytic enzyme.",
                    "Level 2: Active renin acts upon its substrate to generate angiotensin I.",
                    "Level 3: Ang I is cleaved by angiotensin-converting enzyme ACE.",
                ],
                "misconception": "Review the initial sequence of the renin-angiotensin cascade.",
                "mechanistic_explanation": (
                    "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I). "
                    "Ang I is cleaved by angiotensin-converting enzyme (ACE) resulting in physiologically active angiotensin II (Ang II)."
                ),
                "distractor_analysis": None if is_pre else [
                    {
                        "option": "B",
                        "text": "Angiotensin II",
                        "why_incorrect": "Ang I is cleaved by angiotensin-converting enzyme ACE resulting in angiotensin II.",
                        "supported_by_ref": "DOC-PMC-RENAL-0001:C001",
                    },
                    {
                        "option": "C",
                        "text": "Aldosterone",
                        "why_incorrect": "Aldosterone regulates fluid volume and sodium homeostasis.",
                        "supported_by_ref": "DOC-PMC-RENAL-0001:C001",
                    },
                    {
                        "option": "D",
                        "text": "Albumin",
                        "why_incorrect": "Albumin is not the substrate cleaved by active renin.",
                        "supported_by_ref": "DOC-PMC-RENAL-0001:C001",
                    },
                ],
                "revision_summary": "Active renin cleaves angiotensinogen into Angiotensin I, and ACE cleaves Angiotensin I into Angiotensin II.",
                "citations": [
                    {
                        "ref": "DOC-PMC-RENAL-0001:C001",
                        "quote": "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
                        "document_id": "DOC-PMC-RENAL-0001",
                        "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
                    }
                ],
            }
        elif "filtration" in lowered_user or "barrier" in lowered_user or "podocyte" in lowered_user or "basement" in lowered_user:
            default_data = {
                "message": (
                    "The glomerular filtration barrier comprises podocytes, endothelial cells, and the glomerular basement membrane (GBM). "
                    "Podocytes and endothelial cells alone do not guarantee the correct function of the filtration barrier in the absence of a GBM."
                ),
                "socratic_question": "What role does the glomerular basement membrane play in filtration barrier integrity?",
                "hints": [
                    "Level 1: Recall the cellular and extracellular components of the glomerular capillary wall.",
                    "Level 2: Both podocytes and endothelial cells interact with the basement membrane.",
                    "Level 3: The human GBM is characterized by collagen IV and laminins.",
                ],
                "misconception": "Glomerular selectivity involves both the cellular layers and the extracellular basement membrane.",
                "mechanistic_explanation": (
                    "Podocytes and endothelial cells alone do not guarantee the correct function of the filtration barrier in the absence of a GBM. "
                    "Both podocytes and GEC are necessary for the proper assembly of the GBM."
                ),
                "distractor_analysis": None,
                "revision_summary": "Filtration barrier function requires podocytes, endothelial cells, and an intact glomerular basement membrane.",
                "citations": [
                    {
                        "ref": "DOC-PMC-RENAL-0002:C001",
                        "quote": "Podocytes and endothelial cells alone do not guarantee the correct function of the filtration barrier in the absence of a GBM.",
                        "document_id": "DOC-PMC-RENAL-0002",
                        "chunk_id": "DOC-PMC-RENAL-0002-B0017-C01",
                    }
                ],
            }
        else:
            default_data = {
                "message": (
                    "Let us explore the renal physiology principles underlying your query. "
                    "Consider how renal hemodynamics and tubular transport maintain physiological homeostasis."
                ),
                "socratic_question": "What primary Starling force or regulatory mechanism drives this process?",
                "hints": [
                    "Level 1: Recall the basic Starling forces governing glomerular filtration.",
                    "Level 2: Consider the relative vascular resistance of afferent vs efferent arterioles.",
                ],
                "misconception": None,
                "mechanistic_explanation": "Renal hemodynamics are autoregulated through tubuloglomerular feedback and myogenic mechanisms.",
                "distractor_analysis": None,
                "revision_summary": "Autoregulation maintains GFR and renal blood flow across a range of systemic pressures.",
                "citations": [
                    {
                        "ref": "DOC-PMC-RENAL-0001:C001",
                        "quote": "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
                        "document_id": "DOC-PMC-RENAL-0001",
                        "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
                    }
                ],
            }

        latency = (time.perf_counter() - start_t) * 1000.0
        return ProviderResponse(
            raw_text=json.dumps(default_data),
            structured_data=default_data,
            input_tokens=150,
            output_tokens=220,
            latency_ms=round(latency, 2),
            model=self.model_name,
            provider=self.provider_name,
            requested_model=self.model_name,
        )


class GeminiGenerativeProvider:
    """Primary live provider adapter for Google Gemini Flash models via REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        fallback_models: list[str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.provider_name = "google_gemini"
        self.model_name = model_name or os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
        self.fallback_models = (
            fallback_models if fallback_models is not None
            else ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash"]
        )
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.timeout = timeout
        if not self.api_key:
            logger.warning("GeminiGenerativeProvider initialized without API key; live calls will fail.")

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 3000,
    ) -> ProviderResponse:
        import httpx

        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured for live generation.")

        models_to_try = [self.model_name]
        for fb in self.fallback_models:
            if fb not in models_to_try:
                models_to_try.append(fb)

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
            },
        }

        primary_model = self.model_name
        max_retries_per_model = 2
        resp = None
        res_json = None
        last_error = ""
        primary_error: str | None = None
        active_model = primary_model

        start_t = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            for m_idx, current_model in enumerate(models_to_try):
                active_model = current_model
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"

                model_succeeded = False
                for attempt in range(1, max_retries_per_model + 1):
                    try:
                        resp = client.post(url, json=payload, headers=headers)
                        if resp.status_code == 200:
                            try:
                                cand_res = resp.json()
                                cands = cand_res.get("candidates", [])
                                if not cands:
                                    last_error = f"Gemini model {current_model} returned zero candidates."
                                    continue
                                c_parts = cands[0].get("content", {}).get("parts", [])
                                txt = c_parts[0].get("text", "") if c_parts else ""
                                json.loads(txt)
                                res_json = cand_res
                                model_succeeded = True
                                break
                            except Exception as parse_err:
                                last_error = f"Gemini API ({current_model}) returned malformed JSON: {parse_err}"
                                logger.warning(last_error)
                                continue

                        last_error = f"Gemini API ({current_model}) error {resp.status_code}: {resp.text}"
                        # If quota exhausted (429) or high demand (503), try next model or retry
                        if resp.status_code == 429 and "Quota exceeded" in resp.text:
                            logger.warning(f"Model {current_model} Free Tier quota exceeded; failing over to next model.")
                            break

                        if resp.status_code in (429, 503) and attempt < max_retries_per_model:
                            backoff = 2.0 * attempt
                            time.sleep(backoff)
                            continue
                        break
                    except (httpx.RequestError, httpx.TimeoutException) as net_err:
                        last_error = f"Gemini network error ({current_model}): {net_err}"
                        if attempt < max_retries_per_model:
                            time.sleep(2.0 * attempt)
                            continue
                        break

                # Capture the requested/primary model's own failure independently of whatever
                # happens with later fallback models, so reporting never conflates the two.
                if m_idx == 0 and not model_succeeded:
                    primary_error = last_error

                if model_succeeded and res_json is not None:
                    break

            latency_ms = (time.perf_counter() - start_t) * 1000.0

            if not res_json:
                raise RuntimeError(last_error or "All Gemini model candidates failed.")

        # Parse output candidate
        candidates = res_json.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned zero candidates.")

        content_parts = candidates[0].get("content", {}).get("parts", [])
        raw_text = content_parts[0].get("text", "") if content_parts else ""

        usage_meta = res_json.get("usageMetadata", {})
        in_tokens = usage_meta.get("promptTokenCount", 0)
        out_tokens = usage_meta.get("candidatesTokenCount", 0)

        structured = None
        try:
            structured = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse Gemini structured JSON: {exc}")

        return ProviderResponse(
            raw_text=raw_text,
            structured_data=structured,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=round(latency_ms, 2),
            model=active_model,
            provider=self.provider_name,
            requested_model=primary_model,
            provider_failover_applied=(active_model != primary_model),
            primary_provider_error=primary_error,
        )


class OpenAIGenerativeProvider:
    """Optional fallback live provider adapter for OpenAI GPT-5.6 family via REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gpt-5.6-luna",
        timeout: float = 30.0,
    ) -> None:
        self.provider_name = "openai"
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        max_tokens: int = 1500,
    ) -> ProviderResponse:
        import httpx

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured for live generation.")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "tutor_output",
                    "strict": True,
                    "schema": response_schema,
                },
            },
        }

        start_t = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
            latency_ms = (time.perf_counter() - start_t) * 1000.0

            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error {resp.status_code}: {resp.text}")

            res_json = resp.json()

        choices = res_json.get("choices", [])
        if not choices:
            raise RuntimeError("OpenAI returned zero choices.")

        raw_text = choices[0].get("message", {}).get("content", "")
        usage = res_json.get("usage", {})
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)

        structured = None
        try:
            structured = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse OpenAI structured JSON: {exc}")

        return ProviderResponse(
            raw_text=raw_text,
            structured_data=structured,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=round(latency_ms, 2),
            model=self.model_name,
            provider=self.provider_name,
            requested_model=self.model_name,
        )


def get_default_provider() -> GenerativeProvider:
    """Return provider instance according to environment configuration."""
    provider_type = os.environ.get("MEDICALPLAB_TUTOR_PROVIDER", "stub").strip().lower()
    if provider_type in {"gemini", "google"} and (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        return GeminiGenerativeProvider()
    elif provider_type == "openai" and os.environ.get("OPENAI_API_KEY"):
        return OpenAIGenerativeProvider()
    return StubGenerativeProvider()
