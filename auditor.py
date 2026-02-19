import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# ---------- 1) Load environment variables ----------
def load_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)


# ---------- 2) Master prompt (embedded for MVP) ----------
def build_master_prompt(requirement_text: str) -> str:
    """
    This prompt forces the model to act as an auditor and return strict JSON only.
    We embed the API/backend checklist logic here for the MVP.
    """
    return f"""
You are the AI Requirement Clarity Auditor. Your job is to audit requirements for clarity and execution readiness.
You must NOT rewrite the entire requirement document and must NOT invent requirements.
Be strict: if something is not explicitly stated, mark it as missing.

Domain focus: API and backend specifications.

Return ONLY a valid JSON object that matches the schema below.
Do not include markdown. Do not include commentary. Do not include extra keys.

Scoring intent:
The application will compute the final clarity score deterministically.
You must provide honest checklist statuses and gap lists.

API/backend checklist expectations (use these to evaluate completeness):
- Endpoint and HTTP method defined
- Authentication defined
- Authorization and permissions defined
- Request schema defined (fields and types)
- Response schema defined (fields and types)
- Error handling and status codes defined
- Versioning strategy defined
- Pagination strategy defined (if list endpoints)
- Rate limits defined
- Timeouts and retries defined
- Idempotency behavior defined (if create/update)
- Observability requirements defined (logs, metrics, traces)

Edge case expectations (identify which are missing and ask clarifying questions):
- Invalid input formats and ranges
- Missing required fields
- Authentication failure
- Authorization failure
- Not found behavior
- Conflict or concurrency behavior
- Rate limit exceeded
- Upstream dependency timeout or failure
- Duplicate request handling (idempotency)
- Partial failure handling (if multi-step)
- Backward compatibility considerations

Metric expectations (identify which are missing and suggest reasonable metrics):
- Latency target (p95 or p99)
- Throughput target (RPS) or capacity expectation
- Availability or SLA target
- Timeout thresholds
- Error rate budget

JSON schema (must match exactly, keep all fields even if empty):
{{
  "executive_summary": {{
    "top_gaps": [],
    "top_quick_fixes": []
  }},
  "contract_completeness": {{
    "checklist": [
      {{ "item": "", "status": "Yes", "notes": "" }}
    ],
    "missing_items": []
  }},
  "measurability_audit": {{
    "missing_metrics": [],
    "suggested_metrics": [
      {{ "metric": "", "target": "", "notes": "" }}
    ]
  }},
  "ambiguity_flags": [
    {{ "phrase": "", "issue": "", "suggested_rewrite": "" }}
  ],
  "edge_case_coverage": {{
    "missing_edge_cases": [],
    "questions_to_clarify": []
  }},
  "risk_flags": [
    {{ "risk": "", "severity": "Low", "mitigation": "" }}
  ],
  "acceptance_criteria": [
    {{ "given": "", "when": "", "then": "" }}
  ]
}}

Now audit the following requirement document:
\"\"\"{requirement_text}\"\"\"
""".strip()


# ---------- 3) Parse and validate JSON ----------
REQUIRED_TOP_KEYS = {
    "executive_summary",
    "contract_completeness",
    "measurability_audit",
    "ambiguity_flags",
    "edge_case_coverage",
    "risk_flags",
    "acceptance_criteria",
}

def safe_json_loads(text: str) -> dict:
    text = text.strip()

    # direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # try extracting first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        return json.loads(candidate)

    raise ValueError("Model response was not valid JSON.")

def validate_schema(report: dict) -> None:
    missing = REQUIRED_TOP_KEYS - set(report.keys())
    if missing:
        raise ValueError(f"Missing keys in report: {sorted(missing)}")


# ---------- 4) Deterministic hybrid scoring ----------
def compute_clarity_score(report: dict) -> int:
    """
    Score is computed deterministically from the returned JSON fields.
    0 to 100 scale.
    """

    # Contract completeness (30)
    checklist = report.get("contract_completeness", {}).get("checklist", [])
    if checklist:
        yes_count = sum(1 for x in checklist if str(x.get("status", "")).lower() == "yes")
        contract_score = round(30 * (yes_count / max(len(checklist), 1)))
    else:
        contract_score = 0

    # Measurability (20) penalty by missing metrics
    missing_metrics = report.get("measurability_audit", {}).get("missing_metrics", [])
    meas_score = max(20 - 4 * len(missing_metrics), 0)

    # Edge cases (20) penalty by missing edge cases
    missing_edge = report.get("edge_case_coverage", {}).get("missing_edge_cases", [])
    edge_score = max(20 - 2 * len(missing_edge), 0)

    # Ambiguity control (15) penalty by ambiguity flags
    ambiguity_flags = report.get("ambiguity_flags", [])
    amb_score = max(15 - 3 * len(ambiguity_flags), 0)

    # Risk awareness (10) small reward if mitigations exist (bounded)
    risk_flags = report.get("risk_flags", [])
    mitigations = sum(1 for r in risk_flags if (r.get("mitigation") or "").strip())
    risk_score = min(10, 2 * mitigations)

    # Testability (5) based on acceptance criteria count
    ac = report.get("acceptance_criteria", [])
    test_score = 5 if len(ac) >= 3 else (3 if len(ac) >= 1 else 0)

    total = contract_score + meas_score + edge_score + amb_score + risk_score + test_score
    return int(max(0, min(100, total)))

def derive_risk_level(score: int, risk_flags: list[dict]) -> str:
    high = sum(1 for r in risk_flags if str(r.get("severity", "")).lower() == "high")
    if score >= 80 and high == 0:
        return "Low"
    if score < 60 or high >= 2:
        return "High"
    return "Medium"


# ---------- 5) Main audit function ----------
def run_audit(requirement_text: str) -> dict:
    load_env()

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Check your .env file.")

    client = genai.Client(api_key=api_key)

    prompt = build_master_prompt(requirement_text)

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    raw = (resp.text or "").strip()
    report = safe_json_loads(raw)
    validate_schema(report)

    score = compute_clarity_score(report)
    risk_level = derive_risk_level(score, report.get("risk_flags", []))

    # Add score fields for UI
    report["clarity_score"] = score
    report["risk_level"] = risk_level

    return report
