import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv
from google import genai


# -----------------------------
# 1) Environment + Client Setup
# -----------------------------
def load_env() -> None:
    """
    Loads environment variables for local dev and Streamlit Cloud.

    Local:
      - Reads .env from project root (same folder as this file)

    Streamlit Cloud:
      - Reads st.secrets["GEMINI_API_KEY"] if present
      - Optionally reads st.secrets["GEMINI_MODEL"] if present
    """
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Streamlit Cloud secrets override (if available)
    try:
        if "GEMINI_API_KEY" in st.secrets:
            os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
        if "GEMINI_MODEL" in st.secrets:
            os.environ["GEMINI_MODEL"] = st.secrets["GEMINI_MODEL"]
    except Exception:
        # If not running inside Streamlit, st.secrets may not be available
        pass


def get_client_and_model() -> tuple[genai.Client, str]:
    load_env()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Add it to .env (local) or Streamlit Secrets (cloud)."
        )

    # Use a stable default model; you can override via GEMINI_MODEL
    model = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash-lite").strip()

    client = genai.Client(api_key=api_key)
    return client, model


# -----------------------------
# 2) Prompt Construction
# -----------------------------
def build_master_prompt(requirement_text: str) -> str:
    """
    Forces strict JSON-only output and audits API/backend requirement clarity.
    """
    return f"""
You are the AI Requirement Clarity Auditor.

Your job:
Evaluate the requirement for implementation readiness as if you are a senior backend architect reviewing a production API specification.

Be strict. Penalize ambiguity. Penalize missing contracts.

Important constraints:
- Return ONLY valid JSON.
- Output must match the schema EXACTLY.
- Do not include markdown, code fences, or commentary.
- Do not include extra keys.
- Do not include trailing commas.
- Use double quotes for all JSON strings.
- clarity_score must be an integer between 0 and 100.
- risk_level must be exactly one of: Low, Medium, High.
- If the requirement is vague or incomplete, assign a low clarity_score and High risk_level.

Output JSON schema (exact keys required):

{{
  "clarity_score": <integer 0-100>,
  "risk_level": "<Low|Medium|High>",
  "executive_summary": {{
    "top_gaps": [<string>, <string>, <string>],
    "top_quick_fixes": [<string>, <string>, <string>]
  }},
  "contract_completeness": {{
    "checklist": [
      {{
        "item": "<string>",
        "status": "<Yes|No|Partial>",
        "notes": "<string>"
      }}
    ]
  }},
  "measurability_audit": {{
    "missing_metrics": [<string>],
    "suggested_metrics": [<string>]
  }},
  "ambiguity_flags": [
    {{
      "phrase": "<string>",
      "issue": "<string>",
      "suggested_rewrite": "<string>"
    }}
  ],
  "edge_case_coverage": {{
    "missing_edge_cases": [<string>],
    "clarifying_questions": [<string>]
  }},
  "risk_flags": [
    {{
      "risk": "<string>",
      "severity": "<Low|Medium|High>",
      "mitigation": "<string>"
    }}
  ],
  "acceptance_criteria": [
    {{
      "given": "<string>",
      "when": "<string>",
      "then": "<string>"
    }}
  ]
}}

Scoring guidance (use these categories implicitly):
- Contract completeness (endpoints, schemas, auth, errors, versioning)
- Measurability (latency, throughput, SLAs, timeouts, success metrics)
- Edge case coverage (invalid inputs, auth failures, retries, idempotency, dependency failures)
- Ambiguity control (avoid vague terms like fast, scalable, user-friendly without numbers)
- Risk awareness (dependencies, security/compliance, observability)
- Testability (Given/When/Then acceptance criteria)

Risk level guidance:
- High: missing core API contract elements or heavy ambiguity
- Medium: core exists but multiple gaps remain
- Low: clear, measurable, edge-case aware, testable

Requirement text:
\"\"\"{requirement_text}\"\"\"
""".strip()


# -----------------------------
# 3) JSON Extraction + Validation
# -----------------------------
def _extract_json_object(text: str) -> str:
    """
    Attempts to extract the first valid JSON object from a response string.
    """
    text = text.strip()

    # If response is already JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # Otherwise extract first {...} block
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return match.group(0).strip()

    raise ValueError("No JSON object found in model response.")


def _safe_parse_json(text: str) -> Dict[str, Any]:
    raw = _extract_json_object(text)
    return json.loads(raw)


def _default_report() -> Dict[str, Any]:
    """
    Fallback report if the model fails.
    """
    return {
        "clarity_score": 20,
        "risk_level": "High",
        "executive_summary": {
            "top_gaps": [
                "Requirement lacks sufficient detail to be implementation-ready.",
                "Success criteria and measurable targets are missing.",
                "Edge cases and failure handling are not defined.",
            ],
            "top_quick_fixes": [
                "Define endpoints, request/response fields, and authentication approach.",
                "Add measurable performance targets (latency, timeouts, throughput).",
                "Document failure modes and write Given/When/Then acceptance criteria.",
            ],
        },
        "contract_completeness": {
            "checklist": [
                {"item": "Endpoint path and HTTP method defined", "status": "No", "notes": ""},
                {"item": "Authentication/authorization defined", "status": "No", "notes": ""},
                {"item": "Request schema defined", "status": "No", "notes": ""},
                {"item": "Response schema defined", "status": "No", "notes": ""},
                {"item": "Error handling and status codes defined", "status": "No", "notes": ""},
                {"item": "Versioning strategy defined", "status": "No", "notes": ""},
                {"item": "Rate limits/timeouts/retries defined", "status": "No", "notes": ""},
                {"item": "Idempotency behavior defined (if applicable)", "status": "No", "notes": ""},
                {"item": "Observability/logging/metrics defined", "status": "No", "notes": ""},
            ]
        },
        "measurability_audit": {
            "missing_metrics": ["Latency target", "Timeout policy", "Throughput expectations", "Success metric definition"],
            "suggested_metrics": [
                "Define p95 latency target (e.g., <= 250ms) for core endpoints.",
                "Define request timeout and retry behavior (e.g., 3 retries with exponential backoff).",
                "Define throughput or QPS expectation and scaling assumptions.",
                "Define success criteria (e.g., error rate, completion rate, SLO).",
            ],
        },
        "ambiguity_flags": [
            {
                "phrase": "fast / scalable / reliable (if used)",
                "issue": "These are subjective without measurable thresholds.",
                "suggested_rewrite": "Specify measurable targets (latency p95, QPS, error rate, availability).",
            }
        ],
        "edge_case_coverage": {
            "missing_edge_cases": [
                "Invalid or missing required fields",
                "Authentication failures",
                "Dependency timeouts and failures",
                "Duplicate requests and idempotency",
            ],
            "clarifying_questions": [
                "What are the expected error responses and status codes for common failure paths?",
                "What timeouts and retry policies should clients use?",
                "How should the system behave on duplicate create requests?",
            ],
        },
        "risk_flags": [
            {"risk": "Undefined API contract", "severity": "High", "mitigation": "Document endpoints, schemas, auth, and error handling."},
            {"risk": "Unclear success metrics", "severity": "Medium", "mitigation": "Define measurable targets and acceptance criteria."},
        ],
        "acceptance_criteria": [
            {"given": "a valid request payload", "when": "the client calls the endpoint", "then": "the service returns a 2xx response with the expected schema"},
            {"given": "an invalid request payload", "when": "the client calls the endpoint", "then": "the service returns a 4xx response with a standardized error format"},
        ],
    }


def _ensure_required_shape(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures required keys exist so Streamlit UI doesn't crash.
    Fills missing sections with safe defaults.
    """
    base = _default_report()

    def merge(a: Any, b: Any) -> Any:
        # a is default, b is model output
        if isinstance(a, dict) and isinstance(b, dict):
            out = dict(a)
            for k, v in b.items():
                if k in out:
                    out[k] = merge(out[k], v)
                else:
                    out[k] = v
            return out
        return b if b is not None else a

    merged = merge(base, report)

    # Normalize types
    try:
        merged["clarity_score"] = int(merged.get("clarity_score", base["clarity_score"]))
    except Exception:
        merged["clarity_score"] = base["clarity_score"]

    risk = str(merged.get("risk_level", "High")).strip().title()
    if risk not in {"Low", "Medium", "High"}:
        risk = "High"
    merged["risk_level"] = risk

    return merged


# -----------------------------
# 4) Main Audit Function
# -----------------------------
def run_audit(requirement_text: str) -> Dict[str, Any]:
    """
    Main entry point used by app.py.
    Returns a structured dictionary for UI rendering.
    """
    requirement_text = (requirement_text or "").strip()
    if not requirement_text:
        return _default_report()

    client, model = get_client_and_model()
    prompt = build_master_prompt(requirement_text)

    # Retry strategy for JSON compliance
    attempts = 2
    last_error = None

    for _ in range(attempts):
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            # google-genai usually returns text in resp.text
            raw_text = getattr(resp, "text", None)
            if raw_text is None:
                # fallback for some response shapes
                raw_text = str(resp)

            parsed = _safe_parse_json(raw_text)
            shaped = _ensure_required_shape(parsed)
            return shaped

        except Exception as e:
            last_error = e
            # Strengthen prompt for second pass
            prompt = (
                prompt
                + "\n\nReminder: Return ONLY valid JSON exactly matching the schema. No extra text."
            )

    # If all attempts fail, return fallback
    fallback = _default_report()
    fallback["executive_summary"]["top_gaps"][0] = (
        f"Model response could not be parsed as JSON. Using fallback report. Error: {last_error}"
    )
    return fallback