# webapp/app.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route("/analyse", methods=["POST"])
def analyse():
    data = request.json

    if "text" not in data:
        return jsonify({"error": "Missing text"}), 400

    response = requests.post(
        "http://sentiment_service:5000/analyse/sentiment",
        # json=data
        json={"sentence": data["text"]}
    )

    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)