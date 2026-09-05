import os
import json

from google import genai
from google.genai import types

from src.schemas import ClaimReview


MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)


class ClaimReasoner:
    """Use Gemini to review claims using supplied evidence and policy."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)

    def review_claim(
        self,
        claim,
        policy_sections,
        deterministic_findings
    ):
        """
        Review a claim using only supplied claim evidence,
        policy sections, and deterministic findings.
        """

        policy_context = "\n\n".join(
            [
                (
                    f"POLICY SECTION {section['section_id']}: "
                    f"{section['title']}\n"
                    f"{section['text']}"
                )
                for section in policy_sections
            ]
        )

        claim_context = json.dumps(
            claim,
            indent=2
        )

        findings_context = json.dumps(
            deterministic_findings,
            indent=2
        )

        prompt = f"""
You are an insurance claims evidence review assistant.

Your task is to review the claim using ONLY the supplied
claim evidence, deterministic findings, and retrieved policy sections.

Do not invent facts, documents, policy clauses, dates, amounts,
events, or evidence.

========================
IMPORTANT DECISION RULES
========================

The deterministic findings are authoritative for objective checks.

Do NOT override a deterministic finding.

If deterministic findings establish the appropriate decision,
your final decision must remain consistent with them.

Use this decision hierarchy:

1. MATERIAL_CONTRADICTION or UNCERTAIN_CAUSE
   -> ESCALATE

2. MISSING_DOCUMENT
   -> REQUEST_INFORMATION
   unless another higher-priority issue requires ESCALATE or REJECT

3. EXCLUDED_DAMAGE
   -> REJECT

4. CLAIM_WINDOW_EXCEEDED
   -> ESCALATE

5. INSURED_VALUE_EXCEEDED
   -> ESCALATE

6. No material issues and evidence supports coverage
   -> APPROVE

If a required document is missing, do NOT escalate merely because
the claim amount cannot yet be validated. Instead, use
REQUEST_INFORMATION when the missing document can resolve the issue.

========================
EVIDENCE RULES
========================

1. The supplied policy sections are the only policy authority.
2. The supplied claim data is the only source of claim facts.
3. Deterministic findings are objective application checks.
4. Surface material contradictions.
5. Explain significant uncertainty.
6. Every important finding must contain supporting evidence.
7. Claim evidence should cite the actual claim field containing
   the supporting information.
8. Policy findings should identify the relevant policy section.
9. Do not claim that fraud has occurred.
10. Suspicious or contradictory information must be escalated
    for human review.
11. If evidence is insufficient, do not guess.
12. Keep the final decision consistent with the deterministic findings.

========================
CLAIM EVIDENCE
========================

{claim_context}

========================
DETERMINISTIC FINDINGS
========================

{findings_context}

========================
RETRIEVED POLICY SECTIONS
========================

{policy_context}

Produce a structured claim review.

Allowed decisions:

APPROVE
REJECT
REQUEST_INFORMATION
ESCALATE
"""

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ClaimReview,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return ClaimReview.model_validate_json(
            response.text
        )