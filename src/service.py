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

        findings = run_deterministic_checks(
            claim
        )

        initial_decision = determine_initial_decision(
            findings
        )

        query = (
            f"{claim['claim_type']} claim: "
            f"{claim['incident_description']} "
            f"Claimed amount: ₹{claim['claimed_amount']}"
        )

        policy_sections = self.retriever.search(
            query,
            top_k=4
        )

        review = self.reasoner.review_claim(
            claim=claim,
            policy_sections=policy_sections,
            deterministic_findings=findings
        )

        return {
            "claim_id": claim["claim_id"],
            "initial_decision": initial_decision,
            "final_review": review.model_dump(),
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