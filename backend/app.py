"""
app.py
------
Entry point for the Codewise backend Flask application.

Responsibilities:
  - Load environment variables from a .env file via python-dotenv.
  - Initialize the Flask app and enable CORS globally via flask-cors.
  - Register all Flask blueprints (health, docs, query, trigger).
  - Run the development server on port 5000 when executed directly.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from routes.docs import docs_bp
from routes.query import query_bp
from routes.trigger import trigger_bp

# ---------------------------------------------------------------------------
# Environment & App Initialization
# ---------------------------------------------------------------------------

# Load variables from a .env file in the project root (if present).
# This must be called before any os.getenv() calls that depend on .env values.
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes and all origins.
# In production, restrict `origins` to your frontend domain.
CORS(app)

# ---------------------------------------------------------------------------
# Blueprint Registration
# ---------------------------------------------------------------------------

app.register_blueprint(docs_bp)
app.register_blueprint(query_bp)
app.register_blueprint(trigger_bp)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint.

    Returns:
        JSON ``{"status": "ok"}`` with HTTP 200, confirming the server is up.
    """
    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------------------------
# Development Server Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
