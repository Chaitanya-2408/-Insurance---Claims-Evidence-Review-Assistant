import json

from flask import Flask, jsonify, request, send_from_directory

from src.service import ClaimReviewService, CLAIMS_PATH
from src.validation import validate_new_claim


app = Flask(
    __name__,
    static_folder="static"
)


service = ClaimReviewService()


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
    Validate and review a completely new claim supplied by the user.
    """

    data = request.get_json(
        silent=True
    )

    if not data:
        return jsonify({
            "error": "Claim data is required."
        }), 400

    try:

        claim = validate_new_claim(
            data
        )

        result = service.review_claim(
            claim
        )

        result["input_source"] = "new_claim"

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


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8000
    )