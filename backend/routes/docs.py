"""
routes/docs.py
--------------
Blueprint exposing stored documentation records to the frontend.

Endpoints
---------
GET /docs   → returns all documents from the flat-file store as JSON.
"""

from flask import Blueprint, jsonify

from models.doc_store import get_all_docs

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

docs_bp = Blueprint("docs", __name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@docs_bp.route("/docs", methods=["GET"])
def list_docs():
    """Return every document record held in docs.json.

    Responses
    ---------
    200  {"<filename>": {...}, ...}   All stored document records.
    500  {"error": "...", "details": "..."}  Storage layer failure.
    """
    try:
        documents = get_all_docs()
        return jsonify(documents), 200
    except Exception as exc:  # noqa: BLE001
        return (
            jsonify(
                {
                    "error": "Failed to retrieve documents",
                    "details": str(exc),
                }
            ),
            500,
        )
