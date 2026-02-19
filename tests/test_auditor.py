from auditor import run_audit

text = """
Feature: Create Customer API
We need an endpoint to create customer profiles. The API should be fast and secure and handle high volume reliably.
It should return the customer object and handle failures gracefully. Support pagination for listing customers.
"""

report = run_audit(text)
print("Clarity score:", report["clarity_score"])
print("Risk level:", report["risk_level"])
print("Top gaps:", report["executive_summary"]["top_gaps"])