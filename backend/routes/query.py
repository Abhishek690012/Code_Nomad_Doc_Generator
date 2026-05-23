"""
routes/query.py
---------------
Blueprint that accepts a natural-language question and proxies it to the
RAG service provided by the AI engineer.

Endpoints
---------
POST /query   → delegates to ``services.rag.answer(question)``
"""

from flask import Blueprint, jsonify, request

from services import rag

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

query_bp = Blueprint("query", __name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@query_bp.route("/query", methods=["POST"])
def handle_query():
    """Accept a question and return an AI-generated answer via the RAG service.

    Request Body (JSON)
    -------------------
    {
        "question": "<non-empty string>"
    }

    Responses
    ---------
    200  <dict returned by rag.answer()>   Successful answer.
    400  {"error": "..."}                  Missing or invalid payload.
    500  {"error": "...", "details": "..."}  RAG service failure.
    """
    # -- Input validation ----------------------------------------------------
    payload = request.get_json(silent=True)

    if not payload or not payload.get("question", "").strip():
        return (
            jsonify(
                {"error": "A 'question' string is required in the JSON payload."}
            ),
            400,
        )

    question: str = payload["question"].strip()

    # -- RAG delegation -------------------------------------------------------
    try:
        result = rag.answer(question)
        return jsonify(result), 200
    except Exception as exc:  # noqa: BLE001
        return (
            jsonify(
                {
                    "error": "The RAG service encountered an error.",
                    "details": str(exc),
                }
            ),
            500,
        )
