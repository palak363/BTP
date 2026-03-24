from flask import Flask, jsonify
from flask_cors import CORS
import json


app = Flask(__name__)
CORS(app)

@app.route("/iiitd")
def iiitd():
    with open("../data/processed/iiitd_rankings.json") as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)