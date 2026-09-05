from flask import Flask, jsonify, request, send_from_directory

from src.service import ClaimReviewService


app = Flask(__name__, static_folder="static")

service = ClaimReviewService()


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "ClaimGuard AI"
    })


@app.get("/api/claims")
def list_claims():
    return jsonify({
        "message": "Claim listing endpoint will be implemented next."
    })


@app.post("/api/review")
def review_claim():
    data = request.get_json(silent=True) or {}

    claim_id = data.get("claim_id")

    if not claim_id:
        return jsonify({
            "error": "claim_id is required"
        }), 400

    try:
        claim = service.load_claim(claim_id)
        result = service.review_claim(claim)

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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000
    )