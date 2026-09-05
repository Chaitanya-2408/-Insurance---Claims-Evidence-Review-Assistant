from datetime import date, datetime
import math
import re


SUPPORTED_CLAIM_TYPES = {
    "ACCIDENT",
    "THEFT",
    "NATURAL_EVENT"
}

SUPPORTED_DAMAGE_CATEGORIES = {
    "collision",
    "theft",
    "natural_event",
    "mechanical_breakdown",
    "wear_and_tear",
    "internal_mechanical_failure",
    "intentional_damage",
    "unknown"
}


def parse_input_date(value, field_name):
    """Validate and parse an ISO date."""

    if value is None or str(value).strip() == "":
        raise ValueError(
            f"{field_name} is required."
        )

    # Accept a date object as well as the normal UI string.
    if isinstance(value, date) and not isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.strptime(
                str(value).strip(),
                "%Y-%m-%d"
            ).date()

        except (TypeError, ValueError):
            raise ValueError(
                f"{field_name} must use YYYY-MM-DD format."
            )

    if parsed > date.today():
        raise ValueError(
            f"{field_name} cannot be in the future."
        )

    return parsed


def parse_claim_amount(value):
    """
    Convert the incoming claim amount into a valid positive float.

    Accepts values such as:
        125000
        "125000"
        "125,000"
        "₹125000"
        "₹125,000"
    """

    if value is None:
        raise ValueError(
            "Claimed amount must be a valid number."
        )

    # Handle numeric JSON values directly.
    if isinstance(value, bool):
        raise ValueError(
            "Claimed amount must be a valid number."
        )

    if isinstance(value, (int, float)):
        amount = float(value)

    else:
        raw = str(value).strip()

        if not raw:
            raise ValueError(
                "Claimed amount must be a valid number."
            )

        # Remove common formatting.
        raw = (
            raw
            .replace("₹", "")
            .replace(",", "")
            .replace("INR", "")
            .replace("inr", "")
            .strip()
        )

        try:
            amount = float(raw)

        except (TypeError, ValueError):
            raise ValueError(
                "Claimed amount must be a valid number."
            )

    if not math.isfinite(amount):
        raise ValueError(
            "Claimed amount must be a valid number."
        )

    if amount <= 0:
        raise ValueError(
            "Claimed amount must be greater than zero."
        )

    return amount


def validate_new_claim(data):
    """
    Validate and normalize a new claim submitted through the UI.

    This validates input quality only. Policy violations are handled
    later by the deterministic rules engine.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Claim data must be a JSON object."
        )

    # --------------------------------------------------------
    # Claim ID
    # --------------------------------------------------------

    claim_id = str(
        data.get("claim_id", "")
    ).strip().upper()

    if not claim_id:
        raise ValueError(
            "Claim ID is required."
        )

    if not re.fullmatch(
        r"CLM-\d{3,}",
        claim_id
    ):
        raise ValueError(
            "Claim ID must follow the format CLM-001, CLM-002, etc."
        )

    # --------------------------------------------------------
    # Claim type
    # --------------------------------------------------------

    claim_type = str(
        data.get("claim_type", "")
    ).strip().upper()

    if claim_type not in SUPPORTED_CLAIM_TYPES:
        raise ValueError(
            "Claim type must be ACCIDENT, THEFT, or NATURAL_EVENT."
        )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    incident_date = parse_input_date(
        data.get("incident_date"),
        "Incident date"
    )

    reported_date = parse_input_date(
        data.get("reported_date"),
        "Reported date"
    )

    if reported_date < incident_date:
        raise ValueError(
            "Reported date cannot be earlier than incident date."
        )

    # --------------------------------------------------------
    # Claimed amount
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # The frontend/API sends "claim_amount".
    # The internal claim object uses "claimed_amount"
    # because the deterministic rules engine expects that name.
    # --------------------------------------------------------

    raw_amount = data.get("claim_amount")

    claimed_amount = parse_claim_amount(
        raw_amount
    )

    # --------------------------------------------------------
    # Incident description
    # --------------------------------------------------------

    incident_description = str(
        data.get("incident_description", "")
    ).strip()

    if len(incident_description) < 20:
        raise ValueError(
            "Incident description must contain at least 20 characters."
        )

    # --------------------------------------------------------
    # Damage category
    # --------------------------------------------------------

    damage_category = str(
        data.get("damage_category", "")
    ).strip().lower()

    if damage_category not in SUPPORTED_DAMAGE_CATEGORIES:
        raise ValueError(
            "Please select a valid damage category."
        )

    # --------------------------------------------------------
    # Supporting evidence
    # --------------------------------------------------------

    claim_form = str(
        data.get("claim_form", "")
    ).strip()

    repair_estimate = str(
        data.get("repair_estimate", "")
    ).strip()

    fir = str(
        data.get("fir", "")
    ).strip()

    additional_evidence = str(
        data.get("additional_evidence", "")
    ).strip()

    if not claim_form:
        raise ValueError(
            "Claim Form details are required."
        )

    # --------------------------------------------------------
    # Build document list
    # --------------------------------------------------------

    documents = [
        "Claim Form"
    ]

    if repair_estimate:
        documents.append(
            "Repair Estimate"
        )

    if fir:
        documents.append(
            "FIR"
        )

    if incident_description:
        documents.append(
            "Incident Description"
        )

    # --------------------------------------------------------
    # Build internal claim structure
    # --------------------------------------------------------

    claim = {
        "claim_id": claim_id,
        "claim_type": claim_type,
        "incident_date": incident_date.isoformat(),
        "reported_date": reported_date.isoformat(),

        # Keep this name for compatibility with rules.py/service.py.
        "claimed_amount": claimed_amount,

        "damage_category": damage_category,
        "incident_description": incident_description,
        "documents": documents,

        "claim_form": {
            "incident_date": incident_date.isoformat(),
            "details": claim_form
        },

        "repair_estimate": {
            "details": repair_estimate
        } if repair_estimate else {},

        "fir": {
            "details": fir
        } if fir else {},

        "additional_evidence": {
            "details": additional_evidence
        } if additional_evidence else {}
    }

    return claim