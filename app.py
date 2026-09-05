from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "ClaimGuard AI"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)