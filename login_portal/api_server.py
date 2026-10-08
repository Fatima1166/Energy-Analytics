import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, request, jsonify
from flask_cors import CORS
from db_core import authenticate_user, DatabaseConnectionError

app = Flask(__name__)
CORS(app)


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided."}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Please enter both username and password."}), 400

    try:
        user = authenticate_user(username, password)
        if user:
            return jsonify({"success": True, "user": user})
        else:
            return jsonify({"success": False, "message": "Invalid credentials. Please try again."}), 401
    except DatabaseConnectionError as e:
        return jsonify({"success": False, "message": str(e)}), 503


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
