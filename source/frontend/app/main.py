# frontend/app.py
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    text = request.form["text"]

    response = requests.post(
        "http://webapp:8001/analyse",
        json={"text": text}
    )

    result = response.json()
    return render_template("result.html", result=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)