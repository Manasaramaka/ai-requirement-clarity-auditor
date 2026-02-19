import json
import io
import streamlit as st
from auditor import run_audit

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


# ---------------------------
# Theme + Branding
# ---------------------------
def apply_orange_cream_branding(is_dark: bool) -> None:
    if is_dark:
        st.markdown(
            """
            <style>
            :root{
              --bg: #0F0A06;
              --surface: #1A120C;
              --surface-2: #22170F;
              --border: rgba(251, 146, 60, 0.25);
              --text: #FFEAD5;
              --muted: rgba(255, 234, 213, 0.78);
              --orange: #F97316;
              --orange-2: #C2410C;
              --amber: #FDBA74;
              --link: #FDBA74;
              --cream: #FFF7ED;
              --ink: #1F2937;
            }

            .stApp { background-color: var(--bg); }
            .stMarkdown, p, li, span, label, div { color: var(--text) !important; }

            /* Sidebar */
            section[data-testid="stSidebar"] { background-color: var(--surface) !important; }
            section[data-testid="stSidebar"] * { color: var(--text) !important; }

            /* Inputs */
            textarea, input {
              background-color: var(--surface-2) !important;
              color: var(--text) !important;
              border: 1px solid var(--border) !important;
            }

            /* Buttons */
            .stButton button, button[kind="primary"], button[kind="secondary"] {
              background: linear-gradient(135deg, var(--orange), var(--orange-2)) !important;
              color: #ffffff !important;
              border: 1px solid rgba(255,255,255,0.15) !important;
              border-radius: 12px !important;
              padding: 0.7rem 1rem !important;
              font-weight: 650 !important;
            }
            .stButton button:hover { filter: brightness(0.95); }

            /* Expanders */
            details {
              background: var(--surface) !important;
              border: 1px solid var(--border) !important;
              border-radius: 14px !important;
              padding: 6px !important;
            }
            details summary { color: var(--text) !important; font-weight: 650; }

            /* Metrics */
            div[data-testid="stMetric"] {
              background: var(--surface) !important;
              border: 1px solid var(--border) !important;
              border-radius: 14px !important;
              padding: 12px !important;
            }

            a { color: var(--link) !important; }

            /* Hero + cards */
            .hero{
              padding: 18px 20px;
              border-radius: 18px;
              background: linear-gradient(135deg, rgba(249,115,22,0.95), rgba(253,186,116,0.55));
              color: var(--ink);
              box-shadow: 0 14px 40px rgba(0,0,0,0.25);
              border: 1px solid rgba(253,186,116,0.20);
              margin-bottom: 16px;
            }
            .hero h1{ margin:0; font-size:2.2rem; color: var(--ink) !important; }
            .hero p{ margin:6px 0 0 0; color: rgba(31,41,55,0.85) !important; }

            .card{
              background: var(--surface);
              border: 1px solid var(--border);
              border-radius: 16px;
              padding: 14px 16px;
              box-shadow: 0 10px 26px rgba(0,0,0,0.18);
              margin-bottom: 14px;
            }

            .helper {
              color: var(--muted) !important;
              font-size: 0.92rem;
            }

            /* Score ring + wrap (prevents overlap) */
            .score-wrap{
              display:flex;
              gap:16px;
              align-items:flex-start;
              justify-content:flex-start;
              flex-wrap:wrap;
            }
            .ring-wrap{
              display:flex;
              flex-direction:column;
              align-items:center;
              gap:8px;
              min-width: 140px;
            }
            .ring{
              width: 120px;
              height: 120px;
              border-radius: 999px;
              display:flex;
              align-items:center;
              justify-content:center;
              position:relative;
              box-shadow: 0 10px 26px rgba(0,0,0,0.22);
              border: 1px solid rgba(253,186,116,0.20);
              background: #0000;
            }
            .ring::before{
              content:"";
              position:absolute;
              inset:10px;
              border-radius:999px;
              background: var(--surface);
              border: 1px solid rgba(251, 146, 60, 0.18);
            }
            .ring .val{
              position:relative;
              font-size: 30px;
              font-weight: 800;
              color: var(--text);
            }
            .lbl{
              position: static;
              width: auto;
              text-align:center;
              font-size: 0.92rem;
              color: var(--muted);
              margin-top: 6px;
            }
            .badge{
              display:inline-block;
              padding: 6px 12px;
              border-radius: 999px;
              font-size: 0.9rem;
              font-weight: 700;
              border: 1px solid rgba(253,186,116,0.25);
              background: rgba(249,115,22,0.14);
              color: var(--amber);
              height: fit-content;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <style>
            :root{
              --bg: #FFF7ED;
              --surface: #FFFFFF;
              --surface-2: #FFEDD5;
              --border: rgba(194, 65, 12, 0.18);
              --text: #1F2937;
              --muted: rgba(31,41,55,0.72);
              --orange: #F97316;
              --orange-2: #C2410C;
              --amber: #FDBA74;
              --link: #C2410C;
              --cream: #FFF7ED;
              --ink: #1F2937;
            }

            .stApp { background-color: var(--bg); }
            .stMarkdown, p, li, span, label, div { color: var(--text) !important; }

            section[data-testid="stSidebar"] { background-color: var(--surface-2) !important; }
            section[data-testid="stSidebar"] * { color: var(--text) !important; }

            textarea, input {
              background-color: #FFFFFF !important;
              color: var(--text) !important;
              border: 1px solid var(--border) !important;
            }

            .stButton button, button[kind="primary"], button[kind="secondary"] {
              background: linear-gradient(135deg, var(--orange), var(--orange-2)) !important;
              color: #ffffff !important;
              border: 1px solid rgba(0,0,0,0.08) !important;
              border-radius: 12px !important;
              padding: 0.7rem 1rem !important;
              font-weight: 650 !important;
            }
            .stButton button:hover { filter: brightness(0.98); }

            details {
              background: #FFFFFF !important;
              border: 1px solid var(--border) !important;
              border-radius: 14px !important;
              padding: 6px !important;
            }
            details summary { font-weight: 650; }

            div[data-testid="stMetric"] {
              background: #FFFFFF !important;
              border: 1px solid var(--border) !important;
              border-radius: 14px !important;
              padding: 12px !important;
            }

            a { color: var(--link) !important; }

            .hero{
              padding: 18px 20px;
              border-radius: 18px;
              background: linear-gradient(135deg, rgba(249,115,22,0.95), rgba(253,186,116,0.55));
              color: var(--ink);
              box-shadow: 0 14px 34px rgba(194,65,12,0.16);
              border: 1px solid rgba(194,65,12,0.10);
              margin-bottom: 16px;
            }
            .hero h1{ margin:0; font-size:2.2rem; }
            .hero p{ margin:6px 0 0 0; color: rgba(31,41,55,0.78) !important; }

            .card{
              background: #FFFFFF;
              border: 1px solid var(--border);
              border-radius: 16px;
              padding: 14px 16px;
              box-shadow: 0 10px 26px rgba(194,65,12,0.08);
              margin-bottom: 14px;
            }

            .helper {
              color: var(--muted) !important;
              font-size: 0.92rem;
            }

            /* Score ring + wrap (prevents overlap) */
            .score-wrap{
              display:flex;
              gap:16px;
              align-items:flex-start;
              justify-content:flex-start;
              flex-wrap:wrap;
            }
            .ring-wrap{
              display:flex;
              flex-direction:column;
              align-items:center;
              gap:8px;
              min-width: 140px;
            }
            .ring{
              width: 120px;
              height: 120px;
              border-radius: 999px;
              display:flex;
              align-items:center;
              justify-content:center;
              position:relative;
              box-shadow: 0 10px 26px rgba(194,65,12,0.12);
              border: 1px solid rgba(194,65,12,0.10);
              background: #0000;
            }
            .ring::before{
              content:"";
              position:absolute;
              inset:10px;
              border-radius:999px;
              background: #FFFFFF;
              border: 1px solid rgba(194,65,12,0.10);
            }
            .ring .val{
              position:relative;
              font-size: 30px;
              font-weight: 800;
              color: var(--text);
            }
            .lbl{
              position: static;
              width: auto;
              text-align:center;
              font-size: 0.92rem;
              color: var(--muted);
              margin-top: 6px;
            }
            .badge{
              display:inline-block;
              padding: 6px 12px;
              border-radius: 999px;
              font-size: 0.9rem;
              font-weight: 700;
              border: 1px solid rgba(194,65,12,0.18);
              background: rgba(249,115,22,0.12);
              color: #9A3412;
              height: fit-content;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


def score_ring_html(score: int, label: str = "Clarity Score") -> str:
    pct = max(0, min(100, int(score)))
    deg = int(pct * 3.6)
    return f"""
    <div class="ring-wrap">
      <div class="ring" style="background: conic-gradient(#F97316 {deg}deg, rgba(249,115,22,0.18) {deg}deg);">
        <div class="val">{pct}</div>
      </div>
      <div class="lbl">{label}</div>
    </div>
    """


# ---------------------------
# Exports
# ---------------------------
def report_to_json_bytes(report: dict) -> bytes:
    return json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")


def report_to_pdf_bytes(report: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="AI Requirement Clarity Auditor Report",
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    body.spaceAfter = 6

    small = ParagraphStyle(
        "small",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#333333"),
        spaceAfter=4
    )

    story = []
    story.append(Paragraph("AI Requirement Clarity Auditor Report", title_style))
    story.append(Paragraph("Structured audit output for requirement clarity and execution readiness.", small))
    story.append(Spacer(1, 10))

    score = report.get("clarity_score", "")
    risk = report.get("risk_level", "")

    summary_data = [
        ["Clarity Score", str(score)],
        ["Risk Level", str(risk)],
    ]
    summary_table = Table(summary_data, colWidths=[2.0 * inch, 4.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF7ED")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111111")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E7D7C8")),
    ]))
    story.append(Paragraph("Executive Summary", h2))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    def section_list(title: str, items: list[str]) -> None:
        story.append(Paragraph(title, h2))
        if items:
            for it in items[:25]:
                story.append(Paragraph(f"• {it}", body))
        else:
            story.append(Paragraph("• None identified.", body))
        story.append(Spacer(1, 10))

    top_gaps = report.get("executive_summary", {}).get("top_gaps", [])
    top_fixes = report.get("executive_summary", {}).get("top_quick_fixes", [])
    section_list("Key Gaps Identified", top_gaps)
    section_list("Recommended Quick Improvements", top_fixes)

    story.append(Paragraph("Contract Completeness", h2))
    checklist = report.get("contract_completeness", {}).get("checklist", [])
    if checklist:
        rows = [["Item", "Status"]]
        for c in checklist[:30]:
            rows.append([c.get("item", ""), c.get("status", "")])
        t = Table(rows, colWidths=[5.2 * inch, 1.3 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF7ED")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111111")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E7D7C8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFFBF6")]),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("• No checklist results provided.", body))
    story.append(Spacer(1, 12))

    section_list(
        "Measurability Review (Missing Metrics)",
        report.get("measurability_audit", {}).get("missing_metrics", [])
    )

    story.append(Paragraph("Ambiguity Flags", h2))
    flags = report.get("ambiguity_flags", [])
    if flags:
        for fl in flags[:20]:
            story.append(Paragraph(f"• Phrase: {fl.get('phrase','')}", body))
            story.append(Paragraph(f"  Issue: {fl.get('issue','')}", body))
            story.append(Paragraph(f"  Suggested clarification: {fl.get('suggested_rewrite','')}", body))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("• No ambiguity flags detected.", body))
    story.append(Spacer(1, 10))

    section_list(
        "Edge Case Coverage (Missing)",
        report.get("edge_case_coverage", {}).get("missing_edge_cases", [])
    )

    story.append(Paragraph("Risk Assessment", h2))
    risks = report.get("risk_flags", [])
    if risks:
        for r in risks[:25]:
            story.append(Paragraph(f"• {r.get('risk','')} (Severity: {r.get('severity','')})", body))
            mitigation = (r.get("mitigation") or "").strip()
            if mitigation:
                story.append(Paragraph(f"  Mitigation: {mitigation}", body))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("• No significant risks identified.", body))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Acceptance Criteria", h2))
    ac_list = report.get("acceptance_criteria", [])
    if ac_list:
        for ac in ac_list[:20]:
            story.append(Paragraph(f"• Given {ac.get('given','')}", body))
            story.append(Paragraph(f"  When {ac.get('when','')}", body))
            story.append(Paragraph(f"  Then {ac.get('then','')}", body))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("• Acceptance criteria could not be derived from the current specification.", body))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ---------------------------
# Sample requirement (for demos)
# ---------------------------
SAMPLE_REQUIREMENT = """Feature: Create Customer API

Goal
Provide an API endpoint to create a customer profile used by downstream billing and analytics services.

Endpoints
POST /v1/customers

Authentication and Authorization
- Authentication: OAuth 2.0 bearer token required
- Authorization: Only roles "billing_admin" and "support_admin" can create customers

Request Schema
{
  "externalCustomerId": "string (required, max 64)",
  "email": "string (required, valid email format)",
  "phone": "string (optional)",
  "country": "string (required, ISO-3166 alpha-2)",
  "metadata": "object (optional, max 20 keys)"
}

Response Schema
201 Created:
{
  "customerId": "uuid",
  "externalCustomerId": "string",
  "createdAt": "ISO-8601 timestamp"
}

Errors
- 400 for invalid fields (include field-level error details)
- 401 if token is missing/invalid
- 403 if role is not allowed
- 409 if externalCustomerId already exists
- 500 for unexpected server errors

Reliability and Performance
- Latency target: p95 < 250ms, p99 < 500ms
- Availability target: 99.9% monthly
- Timeout: 2s; retries: no automatic retry on POST

Rate Limits
- 60 requests/minute per token

Idempotency
- Support Idempotency-Key header for POST /v1/customers (24-hour window)

Observability
- Log requestId, customerId, errorCode
- Emit metrics for p95 latency, error rate, and rate limit blocks
"""


# ---------------------------
# Streamlit setup
# ---------------------------
st.set_page_config(page_title="AI Requirement Clarity Auditor", layout="wide")

if "report" not in st.session_state:
    st.session_state.report = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "req_text" not in st.session_state:
    st.session_state.req_text = ""
if "is_running" not in st.session_state:
    st.session_state.is_running = False


# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("About")

    st.write(
        "I’m Manasa Ramaka, an analytical problem-solver who builds structured AI systems. "
        "I focus on improving clarity in product decision-making and reducing execution risk "
        "through disciplined evaluation frameworks. This project reflects that approach."
    )

    st.markdown("---")
    st.subheader("Connect")
    st.markdown(
        """
        [LinkedIn](https://www.linkedin.com/in/ramaka-manasa/)  
        [GitHub](https://github.com/Manasaramaka)
        """
    )

    st.markdown("---")
    st.session_state.dark_mode = st.toggle("Dark mode", value=st.session_state.dark_mode)
    st.caption("AI Requirement Clarity Auditor | MVP")

apply_orange_cream_branding(st.session_state.dark_mode)


# ---------------------------
# Hero header
# ---------------------------
st.markdown(
    """
    <div class="hero">
      <h1>AI Requirement Clarity Auditor</h1>
      <p>Evaluate requirement clarity, structural completeness, and delivery risk before development begins.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<p class='helper'>Tip: Use the sample requirement for a fast demo, then export JSON/PDF once the report is generated.</p>",
    unsafe_allow_html=True
)

# ---------------------------
# Controls (fixed alignment)
# ---------------------------
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

b1, b2, b3, b4 = st.columns([1.3, 1.0, 1.0, 1.7])

with b1:
    if st.button("Use Sample", use_container_width=True):
        st.session_state.req_text = SAMPLE_REQUIREMENT
        st.session_state.report = None
        st.session_state.is_running = False
        st.rerun()

with b2:
    run = st.button("Run Audit", use_container_width=True)

with b3:
    clear = st.button("Clear Report", use_container_width=True)

with b4:
    st.caption("Domain: API and backend (MVP)")

if clear:
    st.session_state.report = None
    st.session_state.req_text = ""
    st.session_state.is_running = False
    st.rerun()


# ---------------------------
# Input
# ---------------------------
requirement_text = st.text_area(
    "Paste Requirement Document",
    height=260,
    placeholder="Paste your API or backend requirement here...",
    key="req_text"
)

# Trigger running state (prevents sticky spinner UI)
if run:
    if not requirement_text.strip():
        st.error("Please paste a requirement document before running the audit.")
    else:
        st.session_state.is_running = True
        st.session_state.report = None
        st.rerun()

# Run the audit when state is on
if st.session_state.is_running:
    with st.spinner("Analyzing requirement..."):
        try:
            st.session_state.report = run_audit(st.session_state.req_text)
        except Exception as e:
            st.error(f"Audit failed: {e}")
        finally:
            st.session_state.is_running = False

# Emergency reset (if UI ever looks stuck)
if st.session_state.is_running is False:
    pass


# ---------------------------
# Render report with tabs
# ---------------------------
if st.session_state.report is not None:
    report = st.session_state.report

    json_bytes = report_to_json_bytes(report)
    pdf_bytes = report_to_pdf_bytes(report)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    e1, e2, e3 = st.columns([1, 1, 2])
    with e1:
        st.download_button(
            "Download JSON",
            data=json_bytes,
            file_name="requirement_audit_report.json",
            mime="application/json",
            use_container_width=True
        )
    with e2:
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="requirement_audit_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with e3:
        st.caption("Exports include the full structured report returned by the auditor.")
    st.markdown("</div>", unsafe_allow_html=True)

    tab_summary, tab_contract, tab_meas, tab_amb, tab_edge, tab_risks, tab_ac = st.tabs(
        ["Summary", "Contract", "Measurability", "Ambiguity", "Edge Cases", "Risks", "Acceptance"]
    )

    with tab_summary:
        score = int(report.get("clarity_score", 0))
        risk = report.get("risk_level", "Unknown")

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='score-wrap'>{score_ring_html(score)}<span class='badge'>Risk Level: {risk}</span></div>",
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown("#### Key Gaps Identified")
        gaps = report.get("executive_summary", {}).get("top_gaps", [])
        if gaps:
            for g in gaps:
                st.write(f"- {g}")
        else:
            st.write("No major structural gaps identified.")

        st.markdown("#### Recommended Quick Improvements")
        fixes = report.get("executive_summary", {}).get("top_quick_fixes", [])
        if fixes:
            for f in fixes:
                st.write(f"- {f}")
        else:
            st.write("No immediate improvements suggested.")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_contract:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📘 Contract Completeness")
        checklist = report.get("contract_completeness", {}).get("checklist", [])
        if checklist:
            for item in checklist:
                status = str(item.get("status", "")).lower()
                icon = "✅" if status == "yes" else "❌"
                st.write(f"{icon} {item.get('item','')}")
        else:
            st.write("No checklist results provided.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_meas:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("📈 Measurability Review")
        missing_metrics = report.get("measurability_audit", {}).get("missing_metrics", [])
        if missing_metrics:
            for metric in missing_metrics:
                st.write(f"- Missing: {metric}")
        else:
            st.write("All key performance expectations are defined.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_amb:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("⚠️ Ambiguity Flags")
        flags = report.get("ambiguity_flags", [])
        if flags:
            for flag in flags:
                phrase = flag.get("phrase", "")
                issue = flag.get("issue", "")
                suggestion = flag.get("suggested_rewrite", "")
                with st.expander(f"Phrase: {phrase}"):
                    st.write(f"**Issue:** {issue}")
                    st.write(f"**Suggested Clarification:** {suggestion}")
        else:
            st.write("No ambiguous language detected.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_edge:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🧩 Edge Case Coverage")
        missing_edges = report.get("edge_case_coverage", {}).get("missing_edge_cases", [])
        questions = report.get("edge_case_coverage", {}).get("questions_to_clarify", [])

        if missing_edges:
            st.markdown("#### Missing Edge Cases")
            for edge in missing_edges:
                st.write(f"- {edge}")
        else:
            st.write("Edge case coverage appears sufficient.")

        if questions:
            st.markdown("#### Questions to Clarify")
            for q in questions:
                st.write(f"- {q}")

        st.markdown("</div>", unsafe_allow_html=True)

    with tab_risks:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔍 Risk Assessment")
        risks = report.get("risk_flags", [])
        if risks:
            for risk_item in risks:
                risk_text = risk_item.get("risk", "")
                severity = risk_item.get("severity", "")
                mitigation = (risk_item.get("mitigation") or "").strip()
                with st.expander(f"{risk_text} | Severity: {severity}"):
                    st.write(f"Mitigation: {mitigation if mitigation else 'Not provided.'}")
        else:
            st.write("No significant risks identified.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_ac:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🧪 Acceptance Criteria")
        ac_list = report.get("acceptance_criteria", [])
        if ac_list:
            for ac in ac_list:
                st.write(f"**Given** {ac.get('given','')}")
                st.write(f"**When** {ac.get('when','')}")
                st.write(f"**Then** {ac.get('then','')}")
                st.write("")
        else:
            st.write("Acceptance criteria could not be derived from the current specification.")
        st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption("Built by Manasa Ramaka")
