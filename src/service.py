import json
from pathlib import Path

from src.rules import (
    run_deterministic_checks,
    determine_initial_decision
)
from src.retrieval import PolicyRetriever
from src.llm import ClaimReasoner


CLAIMS_PATH = Path("data/claims")


class ClaimReviewService:
    """Coordinate deterministic checks, retrieval, and Gemini reasoning."""

    def __init__(self):
        self.retriever = PolicyRetriever()
        self.reasoner = ClaimReasoner()

    def load_claim(self, claim_id):
        """Load a claim from the local claim dataset."""

        claim_number = claim_id.split("-")[-1]
        claim_file = CLAIMS_PATH / f"claim_{claim_number}.json"

        if not claim_file.exists():
            raise FileNotFoundError(
                f"Claim not found: {claim_id}"
            )

        with claim_file.open(
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def review_claim(self, claim):
        """Run the complete claim review pipeline."""

        # --------------------------------------------------------
        # Step 1: Deterministic policy checks
        # --------------------------------------------------------

        findings = run_deterministic_checks(
            claim
        )

        initial_decision = determine_initial_decision(
            findings
        )

        try:
            # ----------------------------------------------------
            # Step 2: Retrieve relevant policy sections
            # ----------------------------------------------------

            query = (
                f"{claim['claim_type']} claim: "
                f"{claim['incident_description']} "
                f"Claimed amount: "
                f"INR {claim['claimed_amount']}"
            )

            policy_sections = self.retriever.search(
                query,
                top_k=4
            )

            # ----------------------------------------------------
            # Step 3: Gemini reasoning
            # ----------------------------------------------------

            review = self.reasoner.review_claim(
                claim=claim,
                policy_sections=policy_sections,
                deterministic_findings=findings
            )

            # ----------------------------------------------------
            # Step 4: Keep deterministic findings authoritative
            # ----------------------------------------------------

            final_review = review.model_dump()

            final_review["decision"] = initial_decision

            # Deterministic findings are the authoritative findings.
            # Gemini can provide reasoning and summary, but must not
            # replace objective policy checks.
            final_review["findings"] = self._build_evidence_findings(
                findings
            )

            # ----------------------------------------------------
            # Step 5: Ensure missing information is grounded
            # ----------------------------------------------------

            final_review["missing_information"] = self._get_missing_information(
                findings
            )

            # ----------------------------------------------------
            # Step 6: Ensure uncertainty is grounded
            # ----------------------------------------------------

            final_review["uncertainty"] = self._get_uncertainty(
                findings
            )

            return {
                "claim_id": claim["claim_id"],
                "initial_decision": initial_decision,
                "review_source": "gemini",
                "final_review": final_review,
                "policy_sections": [
                    {
                        "section_id": section["section_id"],
                        "title": section["title"],
                        "score": round(
                            section["score"],
                            4
                        )
                    }
                    for section in policy_sections
                ]
            }

        except Exception as error:

            # ----------------------------------------------------
            # Step 7: Graceful fallback
            # ----------------------------------------------------

            return self._build_fallback_review(
                claim=claim,
                findings=findings,
                initial_decision=initial_decision,
                error=error
            )

    def _build_evidence_findings(self, findings):
        """
        Convert deterministic findings into the structured format
        used by the frontend.

        Deterministic findings are authoritative because they are
        produced directly from claim data and policy rules.
        """

        evidence_findings = []

        for item in findings:

            evidence = [
                {
                    "source": item["source"],
                    "reference": item["reference"],
                    "quote": item["message"]
                }
            ]

            evidence_findings.append(
                {
                    "type": item["type"],
                    "severity": item["severity"],
                    "message": item["message"],
                    "evidence": evidence,
                    "policy_clause": item.get(
                        "policy_clause"
                    )
                }
            )

        return evidence_findings

    def _get_missing_information(self, findings):
        """Return missing documents identified by deterministic checks."""

        missing_information = []

        for item in findings:

            if item["type"] == "MISSING_DOCUMENT":

                missing_information.append(
                    item["message"]
                )

        return missing_information

    def _get_uncertainty(self, findings):
        """Return deterministic reasons requiring additional review."""

        uncertainty_types = {
            "MATERIAL_CONTRADICTION",
            "DATE_CONTRADICTION",
            "UNCERTAIN_CAUSE",
            "CLAIM_WINDOW_EXCEEDED",
            "INSURED_VALUE_EXCEEDED"
        }

        uncertainty = []

        for item in findings:

            if item["type"] in uncertainty_types:

                uncertainty.append(
                    item["message"]
                )

        return uncertainty

    def _build_fallback_review(
        self,
        claim,
        findings,
        initial_decision,
        error
    ):
        """
        Build a deterministic review when Gemini is unavailable.

        Temporary Gemini failures such as 429 or 503 must not
        break the claim review application.
        """

        error_text = str(error)

        # --------------------------------------------------------
        # Identify Gemini availability problem
        # --------------------------------------------------------

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
        ):
            availability_message = (
                "Gemini API quota is temporarily unavailable. "
                "The decision below is based on deterministic "
                "policy checks only."
            )

        elif (
            "503" in error_text
            or "UNAVAILABLE" in error_text
        ):
            availability_message = (
                "Gemini API is temporarily unavailable. "
                "The decision below is based on deterministic "
                "policy checks only."
            )

        else:
            availability_message = (
                "Gemini reasoning was unavailable. "
                "The decision below is based on deterministic "
                "policy checks only."
            )

        # --------------------------------------------------------
        # Build grounded findings
        # --------------------------------------------------------

        evidence_findings = self._build_evidence_findings(
            findings
        )

        missing_information = self._get_missing_information(
            findings
        )

        uncertainty = self._get_uncertainty(
            findings
        )

        # --------------------------------------------------------
        # Build fallback summary
        # --------------------------------------------------------

        summary = (
            f"{availability_message} "
            f"Initial deterministic decision: "
            f"{initial_decision}."
        )

        # --------------------------------------------------------
        # Return structured fallback response
        # --------------------------------------------------------

        return {
            "claim_id": claim["claim_id"],
            "initial_decision": initial_decision,
            "review_source": "deterministic_fallback",
            "ai_error": availability_message,
            "final_review": {
                "decision": initial_decision,
                "summary": summary,
                "findings": evidence_findings,
                "missing_information": missing_information,
                "uncertainty": uncertainty
            },
            "policy_sections": []
        }