"""
routes/trigger.py
-----------------
Blueprint that orchestrates the full documentation generation pipeline.

Pipeline (POST /trigger)
------------------------
1. Validate the incoming ``repo`` and ``files`` payload.
2. For every file path in ``files``:
   a. Fetch raw content from GitHub via ``fetch_file_content``.
   b. Generate structured documentation via ``doc_generator.generate``.
   c. Persist the result with ``save_doc``.
3. Retrieve all stored documents with ``get_all_docs``.
4. Rebuild the vector search index with ``index_store.add_docs``.
5. Return the complete documentation dictionary as JSON.

All AI/ML logic (``doc_generator``, ``index_store``) is provided by Role A
and is intentionally not implemented here.
"""

import logging

from flask import Blueprint, jsonify, request

from services.github_client import fetch_file_content
from services import doc_generator, index_store
from models.doc_store import save_doc, get_all_docs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

trigger_bp = Blueprint("trigger", __name__)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@trigger_bp.route("/trigger", methods=["POST"])
def trigger_pipeline():
    """Run the full documentation generation pipeline for a list of files.

    Request Body (JSON)
    -------------------
    {
        "repo":  "<owner>/<repository>",        # e.g. "octocat/Hello-World"
        "files": ["path/to/file.py", ...]       # non-empty list of strings
    }

    Responses
    ---------
    200  { "<filepath>": { ...doc... }, ... }    All stored documents after run.
    400  { "error": "<validation message>" }      Invalid or missing payload.
    500  { "error": "Pipeline failed",
           "details": "<exception message>" }     Any pipeline stage failure.
    """
    # -- Input Validation ----------------------------------------------------
    payload = request.get_json(silent=True)

    if not payload:
        return (
            jsonify({"error": "Request body must be a valid JSON object."}),
            400,
        )

    repo = payload.get("repo", "")
    files = payload.get("files")

    if not isinstance(repo, str) or not repo.strip():
        return (
            jsonify(
                {
                    "error": (
                        "'repo' is required and must be a non-empty string "
                        "in 'owner/repo' format."
                    )
                }
            ),
            400,
        )

    if not isinstance(files, list) or not files:
        return (
            jsonify(
                {
                    "error": (
                        "'files' is required and must be a non-empty list of "
                        "file path strings."
                    )
                }
            ),
            400,
        )

    invalid_entries = [f for f in files if not isinstance(f, str) or not f.strip()]
    if invalid_entries:
        return (
            jsonify(
                {
                    "error": (
                        "All entries in 'files' must be non-empty strings. "
                        f"Invalid entries found: {invalid_entries}"
                    )
                }
            ),
            400,
        )

    repo = repo.strip()

    # -- Pipeline ------------------------------------------------------------
    try:
        for filepath in files:
            filepath = filepath.strip()

            logger.info("[trigger] Fetching '%s' from repo '%s'.", filepath, repo)
            content = fetch_file_content(repo, filepath)

            logger.info("[trigger] Generating documentation for '%s'.", filepath)
            generated_doc = doc_generator.generate(filepath, content)

            logger.info("[trigger] Saving documentation for '%s'.", filepath)
            save_doc(filepath, generated_doc)

        logger.info("[trigger] Retrieving full document store for indexing.")
        all_docs = get_all_docs()

        logger.info("[trigger] Rebuilding vector search index.")
        index_store.add_docs(all_docs)

        logger.info("[trigger] Pipeline completed successfully for repo '%s'.", repo)
        return jsonify(all_docs), 200

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "[trigger] Pipeline failed for repo '%s': %s",
            repo,
            exc,
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "error": "Pipeline failed",
                    "details": str(exc),
                }
            ),
            500,
        )
