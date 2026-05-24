"""
verify_integration.py
---------------------
Standalone test client for the Codewise backend API.

Runs three sequential checks against the locally running Flask server at
http://localhost:5000 to validate the complete integration between the
infrastructure routes and the AI services provided by Role A.

Usage
-----
    # In one terminal, start the Flask server:
    #   cd backend && python app.py

    # In another terminal, run this script:
    #   python verify_integration.py

Requirements
------------
    pip install requests
"""

import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:5000"

# Lightweight, public GitHub repo used as a realistic test fixture.
TEST_REPO  = "octocat/Hello-World"
TEST_FILES = ["README"]          # The root-level README (no extension needed)
TEST_QUESTION = "What is this repository about?"

SEPARATOR = "=" * 60


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _header(title: str) -> None:
    """Print a clearly visible section header."""
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def _ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def _fail(msg: str) -> None:
    print(f"  ❌  {msg}")


def _info(label: str, value) -> None:
    print(f"  ℹ️   {label}: {value}")


# ---------------------------------------------------------------------------
# Step 1 — POST /trigger
# ---------------------------------------------------------------------------

def test_trigger() -> None:
    """
    Sends a repo + file list to /trigger and validates the pipeline ran
    end-to-end (fetch → LLM generation → save → FAISS indexing).
    """
    _header("STEP 1 — POST /trigger  (Trigger Pipeline)")

    payload = {"repo": TEST_REPO, "files": TEST_FILES}
    _info("Request payload", payload)

    try:
        response = requests.post(
            f"{BASE_URL}/trigger",
            json=payload,
            timeout=120,          # LLM calls can be slow; give it 2 minutes
        )
    except requests.exceptions.ConnectionError:
        _fail(
            "Could not connect to the Flask server at "
            f"{BASE_URL}. Is it running?"
        )
        sys.exit(1)

    _info("HTTP status", response.status_code)

    if response.status_code != 200:
        _fail("Pipeline did not return HTTP 200.")
        _info("Response body", response.text)
        sys.exit(1)

    _ok("Pipeline completed successfully (HTTP 200).")
    _info(
        "Files indexed",
        list(response.json().keys()),
    )


# ---------------------------------------------------------------------------
# Step 2 — GET /docs
# ---------------------------------------------------------------------------

def test_docs() -> None:
    """
    Retrieves all stored documents from /docs and confirms the README entry
    has the expected shape: { summary: str, functions: list }.
    """
    _header("STEP 2 — GET /docs  (Document Retrieval)")

    # Brief pause so any async file I/O has time to settle.
    time.sleep(1)

    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=30)
    except requests.exceptions.ConnectionError:
        _fail(f"Could not connect to {BASE_URL}/docs.")
        sys.exit(1)

    _info("HTTP status", response.status_code)

    if response.status_code != 200:
        _fail("/docs did not return HTTP 200.")
        _info("Response body", response.text)
        sys.exit(1)

    data = response.json()

    # --- Shape check: response must be a dict ---
    if not isinstance(data, dict):
        _fail(
            f"Expected a dict from /docs, got {type(data).__name__}."
        )
        sys.exit(1)

    _ok("Response is a dict.")
    _info("All stored file keys", list(data.keys()))

    # --- Key check: our test file must be present ---
    # The key may be stored exactly as sent ("README") or with a path prefix;
    # we do a flexible substring match so the test is robust to minor
    # implementation differences.
    matched_key = next(
        (k for k in data if TEST_FILES[0] in k),
        None,
    )

    if matched_key is None:
        _fail(
            f"'{TEST_FILES[0]}' was not found in the document store. "
            f"Available keys: {list(data.keys())}"
        )
        sys.exit(1)

    _ok(f"Found expected file in store under key: '{matched_key}'")
    doc = data[matched_key]

    # --- Field check: summary (str) ---
    summary = doc.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        _fail(
            f"Expected 'summary' to be a non-empty string, got: {summary!r}"
        )
        sys.exit(1)

    _ok("'summary' field is a non-empty string.")
    print(f"\n  📄  LLM-generated summary:\n")
    print(f"      {summary}\n")

    # --- Field check: functions (list) ---
    functions = doc.get("functions")
    if not isinstance(functions, list):
        _fail(
            f"Expected 'functions' to be a list, got: {type(functions).__name__}"
        )
        sys.exit(1)

    _ok(f"'functions' field is a list ({len(functions)} entries).")


# ---------------------------------------------------------------------------
# Step 3 — POST /query
# ---------------------------------------------------------------------------

def test_query() -> None:
    """
    Sends a natural-language question to /query and validates the RAG
    pipeline returns the keys the frontend expects:
        answer, source_file, source_function
    """
    _header("STEP 3 — POST /query  (RAG Pipeline)")

    payload = {"question": TEST_QUESTION}
    _info("Question", TEST_QUESTION)

    try:
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        _fail(f"Could not connect to {BASE_URL}/query.")
        sys.exit(1)

    _info("HTTP status", response.status_code)

    if response.status_code != 200:
        _fail("/query did not return HTTP 200.")
        _info("Response body", response.text)
        sys.exit(1)

    _ok("RAG endpoint returned HTTP 200.")

    result = response.json()

    # --- Key presence check ---
    expected_keys = {"answer", "source_file", "source_function"}
    missing_keys = expected_keys - set(result.keys())

    if missing_keys:
        _fail(
            f"The following expected keys are missing from the response: "
            f"{missing_keys}"
        )
        _info("Actual response keys", list(result.keys()))
        sys.exit(1)

    _ok(f"All expected keys present: {sorted(expected_keys)}")

    # --- Print the AI-generated answer and citation ---
    print(f"\n  🤖  AI-generated answer:\n")
    print(f"      {result['answer']}\n")
    print(f"  📌  Citation:")
    _info("source_file",     result["source_file"])
    _info("source_function", result["source_function"])


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{'=' * 60}")
    print("  Codewise — Backend Integration Verification")
    print(f"  Target server : {BASE_URL}")
    print(f"  Test repo     : {TEST_REPO}")
    print(f"  Test file(s)  : {TEST_FILES}")
    print(f"{'=' * 60}")

    test_trigger()
    test_docs()
    test_query()

    _header("ALL STEPS PASSED ✅")
    print("  The backend pipeline is fully operational.\n")


if __name__ == "__main__":
    main()
