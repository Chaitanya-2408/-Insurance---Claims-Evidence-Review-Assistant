from datetime import datetime


# ============================================================
# Helper Functions
# ============================================================

def parse_date(date_string):
    """Convert YYYY-MM-DD into a date object."""
    return datetime.strptime(
        date_string,
        "%Y-%m-%d"
    ).date()


def finding(
    finding_type,
    severity,
    message,
    source,
    reference,
    policy_clause=None
):
    """Create a standard deterministic finding object."""

    return {
        "type": finding_type,
        "severity": severity,
        "message": message,
        "source": source,
        "reference": reference,
        "policy_clause": policy_clause
    }


# ============================================================
# 1. Required Document Check
# ============================================================

def check_required_documents(claim):
    """
    Check whether all documents required for the claim type
    are available.
    """

    required_documents = {
        "ACCIDENT": [
            "Claim Form",
            "Repair Estimate",
            "Incident Description"
        ],
        "THEFT": [
            "Claim Form",
            "FIR",
            "Incident Description"
        ],
        "NATURAL_EVENT": [
            "Claim Form",
            "Repair Estimate",
            "Incident Description"
        ]
    }

    claim_type = claim.get(
        "claim_type"
    )

    required = required_documents.get(
        claim_type,
        []
    )

    submitted = set(
        claim.get(
            "documents",
            []
        )
    )

    findings = []

    for document in required:

        if document not in submitted:

            findings.append(
                finding(
                    "MISSING_DOCUMENT",
                    "HIGH",
                    f"Required document is missing: {document}",
                    "Claim",
                    "documents",
                    "POLICY SECTION 4: REQUIRED DOCUMENTS"
                )
            )

    return findings


# ============================================================
# 2. Claim Reporting Window
# ============================================================

def check_claim_reporting_window(claim):
    """
    Check whether the claim was reported within
    the policy's 7-day reporting window.
    """

    incident_date = parse_date(
        claim["incident_date"]
    )

    reported_date = parse_date(
        claim["reported_date"]
    )

    days_taken = (
        reported_date - incident_date
    ).days

    allowed_days = 7

    if days_taken > allowed_days:

        return [
            finding(
                "CLAIM_WINDOW_EXCEEDED",
                "HIGH",
                (
                    f"Claim was reported {days_taken} days "
                    f"after the incident. Policy allows "
                    f"{allowed_days} days."
                ),
                "Claim",
                "incident_date/reported_date",
                "POLICY SECTION 3: CLAIM REPORTING WINDOW"
            )
        ]

    return []


# ============================================================
# 3. Insured Value Check
# ============================================================

def check_insured_value(claim):
    """
    Check whether claimed amount exceeds the policy IDV.
    """

    claimed_amount = float(
        claim.get(
            "claimed_amount",
            0
        )
    )

    insured_value = 500000

    if claimed_amount > insured_value:

        return [
            finding(
                "INSURED_VALUE_EXCEEDED",
                "HIGH",
                (
                    f"Claimed amount ₹{claimed_amount:,.2f} "
                    f"exceeds the insured value of "
                    f"₹{insured_value:,.2f}."
                ),
                "Claim",
                "claimed_amount",
                "POLICY SECTION 2: INSURED VALUE"
            )
        ]

    return []


# ============================================================
# 4. Exclusion Check
# ============================================================

def check_exclusions(claim):
    """
    Check whether the claimed damage falls under
    a known policy exclusion.
    """

    exclusions = {
        "mechanical_breakdown",
        "wear_and_tear",
        "internal_mechanical_failure",
        "intentional_damage"
    }

    damage_category = claim.get(
        "damage_category"
    )

    if damage_category in exclusions:

        return [
            finding(
                "EXCLUDED_DAMAGE",
                "HIGH",
                (
                    f"Damage category "
                    f"'{damage_category}' is excluded "
                    f"under the policy."
                ),
                "Claim",
                "damage_category",
                "POLICY SECTION 5: EXCLUSIONS"
            )
        ]

    return []


# ============================================================
# 5. Contradiction Check
# ============================================================

def check_contradictions(claim):
    """
    Detect material contradictions between available
    claim evidence.
    """

    findings = []

    claim_form = claim.get(
        "claim_form",
        {}
    )

    incident_date = claim.get(
        "incident_date"
    )

    form_date = claim_form.get(
        "incident_date"
    )

    # --------------------------------------------------------
    # Check claim record vs claim form
    # --------------------------------------------------------

    if (
        incident_date
        and form_date
        and incident_date != form_date
    ):

        findings.append(
            finding(
                "DATE_CONTRADICTION",
                "CRITICAL",
                (
                    "Incident date in the claim record "
                    "does not match the claim form."
                ),
                "Claim",
                "incident_date vs claim_form.incident_date",
                "POLICY SECTION 7: CONTRADICTORY INFORMATION"
            )
        )

    # --------------------------------------------------------
    # Check additional evidence
    # --------------------------------------------------------

    additional_evidence = claim.get(
        "additional_evidence",
        {}
    )

    evidence_date = additional_evidence.get(
        "incident_date"
    )

    if (
        incident_date
        and evidence_date
        and incident_date != evidence_date
    ):

        findings.append(
            finding(
                "MATERIAL_CONTRADICTION",
                "CRITICAL",
                (
                    "Additional evidence gives a different "
                    "incident date from the claim record."
                ),
                "Additional Evidence",
                "incident_date vs additional_evidence.incident_date",
                "POLICY SECTION 7: CONTRADICTORY INFORMATION"
            )
        )

    return findings


# ============================================================
# 6. Unknown Cause Check
# ============================================================

def check_uncertain_cause(claim):
    """
    Detect claims where the available evidence does not
    establish the cause of damage.
    """

    damage_category = claim.get(
        "damage_category"
    )

    description = claim.get(
        "incident_description",
        ""
    ).lower()

    if (
        damage_category in [
            None,
            "",
            "unknown"
        ]
        or "does not know" in description
        or "unknown" in description
        or "unclear" in description
    ):

        return [
            finding(
                "UNCERTAIN_CAUSE",
                "HIGH",
                (
                    "Available evidence does not establish "
                    "the cause of the vehicle damage."
                ),
                "Incident Description",
                "incident_description",
                "POLICY SECTION 8: UNCERTAINTY AND MANUAL REVIEW"
            )
        ]

    return []


# ============================================================
# Main Rules Engine
# ============================================================

def run_deterministic_checks(claim):
    """
    Execute all deterministic checks for a claim.
    """

    findings = []

    findings.extend(
        check_required_documents(
            claim
        )
    )

    findings.extend(
        check_claim_reporting_window(
            claim
        )
    )

    findings.extend(
        check_insured_value(
            claim
        )
    )

    findings.extend(
        check_exclusions(
            claim
        )
    )

    findings.extend(
        check_contradictions(
            claim
        )
    )

    findings.extend(
        check_uncertain_cause(
            claim
        )
    )

    return findings


# ============================================================
# Deterministic Decision
# ============================================================

def determine_initial_decision(findings):
    """
    Generate a preliminary decision based only on
    deterministic findings.

    Gemini will NOT override these objective findings
    without evidence.
    """

    finding_types = {
        item["type"]
        for item in findings
    }

    # --------------------------------------------------------
    # Highest priority: contradictions
    # --------------------------------------------------------

    if "MATERIAL_CONTRADICTION" in finding_types:
        return "ESCALATE"

    if "DATE_CONTRADICTION" in finding_types:
        return "ESCALATE"

    # --------------------------------------------------------
    # Unknown / uncertain cause
    # --------------------------------------------------------

    if "UNCERTAIN_CAUSE" in finding_types:
        return "ESCALATE"

    # --------------------------------------------------------
    # Missing evidence
    # --------------------------------------------------------

    if "MISSING_DOCUMENT" in finding_types:
        return "REQUEST_INFORMATION"

    # --------------------------------------------------------
    # Excluded damage
    # --------------------------------------------------------

    if "EXCLUDED_DAMAGE" in finding_types:
        return "REJECT"

    # --------------------------------------------------------
    # Reporting window exceeded
    # --------------------------------------------------------

    if "CLAIM_WINDOW_EXCEEDED" in finding_types:
        return "ESCALATE"

    # --------------------------------------------------------
    # Insured value exceeded
    # --------------------------------------------------------

    if "INSURED_VALUE_EXCEEDED" in finding_types:
        return "ESCALATE"

    # --------------------------------------------------------
    # No deterministic issues
    # --------------------------------------------------------

    return "APPROVE"