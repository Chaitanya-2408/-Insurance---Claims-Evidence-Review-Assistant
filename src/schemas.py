from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str
    reference: str
    quote: str


class Finding(BaseModel):
    type: str
    severity: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
    message: str
    evidence: list[Evidence] = Field(
        default_factory=list
    )
    policy_clause: str | None = None


class ClaimReview(BaseModel):
    decision: Literal[
        "APPROVE",
        "REJECT",
        "REQUEST_INFORMATION",
        "ESCALATE"
    ]

    summary: str

    findings: list[Finding] = Field(
        default_factory=list
    )

    missing_information: list[str] = Field(
        default_factory=list
    )

    uncertainty: list[str] = Field(
        default_factory=list
    )