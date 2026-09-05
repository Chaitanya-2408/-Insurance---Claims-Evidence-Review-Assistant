import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from src.service import ClaimReviewService, CLAIMS_PATH
from src.validation import validate_new_claim
from src.document_parser import extract_document_text


# ============================================================
# Environment configuration
# ============================================================

def load_gemini_api_key():
    """
    Load GEMINI_API_KEY automatically.

    Priority:
    1. Existing environment variable
    2. .env
    3. .env.example

    The evaluator can place their Gemini API key in
    .env.example and run:

        python app.py
    """

    # Keep a real environment variable if already provided.
    existing_key = os.getenv("GEMINI_API_KEY", "").strip()

    if existing_key and existing_key not in {
        "YOUR_GEMINI_API_KEY",
        "YOUR_API_KEY",
        "PASTE_YOUR_API_KEY_HERE"
    }:
        return

    project_root = Path(__file__).resolve().parent

    for filename in [".env", ".env.example"]:

        env_file = project_root / filename

        if not env_file.exists():
            continue

        try:
            for line in env_file.read_text(
                encoding="utf-8"
            ).splitlines():

                line = line.strip()

                if (
                    not line
                    or line.startswith("#")
                    or "=" not in line
                ):
                    continue

                key_name, key_value = line.split(
                    "=",
                    1
                )

                key_name = key_name.strip()
                key_value = key_value.strip().strip("\"'")

                if key_name != "GEMINI_API_KEY":
                    continue

                if key_value in {
                    "",
                    "YOUR_GEMINI_API_KEY",
                    "YOUR_API_KEY",
                    "PASTE_YOUR_API_KEY_HERE"
                }:
                    continue

                os.environ["GEMINI_API_KEY"] = key_value
                return

        except OSError:
            continue

# Load API key BEFORE creating ClaimReviewService.
load_gemini_api_key()


# ============================================================
# Flask application
# ============================================================

app = Flask(
    __name__,
    static_folder="static"
)


service = ClaimReviewService()


# ============================================================
# Routes
# ============================================================

@app.get("/")
def home():
    return send_from_directory(
        "static",
        "index.html"
    )


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "ClaimGuard AI"
    })


@app.get("/api/claims")
def list_claims():
    """Return the available predefined demo claims."""

    claims = []

    for claim_file in sorted(
        CLAIMS_PATH.glob("claim_*.json")
    ):
        try:

            with claim_file.open(
                "r",
                encoding="utf-8"
            ) as file:

                claim = json.load(file)

            claims.append({
                "claim_id": claim["claim_id"],
                "claim_type": claim["claim_type"],
                "incident_description": claim[
                    "incident_description"
                ],
                "claimed_amount": claim[
                    "claimed_amount"
                ]
            })

        except (
            OSError,
            json.JSONDecodeError,
            KeyError
        ):
            continue

    return jsonify({
        "claims": claims
    })


@app.post("/api/review")
def review_claim():
    """
    Review one of the predefined demo claims.
    """

    data = request.get_json(
        silent=True
    ) or {}

    claim_id = data.get(
        "claim_id"
    )

    if not claim_id:
        return jsonify({
            "error": "claim_id is required"
        }), 400

    try:

        claim = service.load_claim(
            claim_id
        )

        result = service.review_claim(
            claim
        )

        return jsonify(result)

    except FileNotFoundError as error:

        return jsonify({
            "error": str(error)
        }), 404

    except Exception as error:

        return jsonify({
            "error": "Claim review failed",
            "details": str(error)
        }), 500


@app.post("/api/review-new")
def review_new_claim():
    """
    Validate and review a completely new claim supplied
    by the user.

    Supports PDF/TXT evidence uploads.
    """

    try:

        # ----------------------------------------------------
        # Read normal form fields
        # ----------------------------------------------------

        data = {
            "claim_id": request.form.get(
                "claim_id"
            ),
            "claim_type": request.form.get(
                "claim_type"
            ),
            "incident_date": request.form.get(
                "incident_date"
            ),
            "reported_date": request.form.get(
                "reported_date"
            ),
            "claim_amount": request.form.get(
                "claim_amount"
            ),
            "damage_category": request.form.get(
                "damage_category"
            ),
            "incident_description": request.form.get(
                "incident_description"
            ),
            "additional_evidence": request.form.get(
                "additional_evidence",
                ""
            )
        }

        # ----------------------------------------------------
        # Extract Claim Form
        # ----------------------------------------------------

        claim_form_file = request.files.get(
            "claim_form_file"
        )

        if claim_form_file:

            data["claim_form"] = (
                extract_document_text(
                    claim_form_file
                )
            )

        else:

            data["claim_form"] = request.form.get(
                "claim_form",
                ""
            )

        # ----------------------------------------------------
        # Extract Repair Estimate
        # ----------------------------------------------------

        repair_file = request.files.get(
            "repair_estimate_file"
        )

        if repair_file:

            data["repair_estimate"] = (
                extract_document_text(
                    repair_file
                )
            )

        else:

            data["repair_estimate"] = request.form.get(
                "repair_estimate",
                ""
            )

        # ----------------------------------------------------
        # Extract FIR
        # ----------------------------------------------------

        fir_file = request.files.get(
            "fir_file"
        )

        if fir_file:

            data["fir"] = (
                extract_document_text(
                    fir_file
                )
            )

        else:

            data["fir"] = request.form.get(
                "fir",
                ""
            )

        # ----------------------------------------------------
        # Validate using existing validation pipeline
        # ----------------------------------------------------

        claim = validate_new_claim(
            data
        )

        # ----------------------------------------------------
        # Existing review pipeline
        # ----------------------------------------------------

        result = service.review_claim(
            claim
        )

        result["input_source"] = (
            "uploaded_documents"
        )

        return jsonify(result)

    except ValueError as error:

        return jsonify({
            "error": str(error)
        }), 400

    except Exception as error:

        return jsonify({
            "error": "New claim review failed",
            "details": str(error)
        }), 500


# ============================================================
# Application entry point
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000
    )