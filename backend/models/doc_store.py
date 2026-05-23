"""
models/doc_store.py
-------------------
Flat-file storage layer for Codewise.

All documentation records are persisted as a single JSON object in
``data/docs.json``, keyed by filename.  This module is strictly a
file I/O helper — it contains no LLM, AI, or Flask routing logic.

Schema (docs.json)::

    {
        "<filename>": { ...doc dict... },
        ...
    }

Functions
---------
save_doc(filename, doc)  → None
get_all_docs()           → dict
get_doc(filename)        → dict | None
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storage Paths
# ---------------------------------------------------------------------------

# Resolve paths relative to *this file* so the module works regardless of
# where the process is launched from.
_BACKEND_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = _BACKEND_DIR / "data"
DOCS_FILE: Path = DATA_DIR / "docs.json"


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _ensure_store() -> None:
    """Create data/ and docs.json if they do not already exist.

    Called at the start of every public function so callers never have to
    worry about bootstrapping the storage layer manually.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DOCS_FILE.exists():
        DOCS_FILE.write_text("{}\n", encoding="utf-8")
        logger.info("Initialised empty doc store at %s", DOCS_FILE)


def _read_store() -> dict[str, Any]:
    """Read and parse docs.json, returning the contents as a dict.

    Returns an empty dict and logs a warning when the file contains
    malformed JSON rather than crashing the caller.
    """
    try:
        text = DOCS_FILE.read_text(encoding="utf-8").strip()
        if not text:
            return {}
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning(
            "docs.json contains malformed JSON (%s). "
            "Treating store as empty to prevent data corruption.",
            exc,
        )
        return {}


def _write_store(data: dict[str, Any]) -> None:
    """Serialise *data* and write it atomically to docs.json.

    Uses a write-then-replace strategy (via a sibling temp file) to
    minimise the risk of leaving a half-written file on disk.
    """
    tmp_path = DOCS_FILE.with_suffix(".json.tmp")
    try:
        tmp_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(DOCS_FILE)  # atomic on POSIX systems
    except OSError as exc:
        logger.error("Failed to write doc store: %s", exc)
        # Clean up temp file if it was left behind.
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_doc(filename: str, doc: dict[str, Any]) -> None:
    """Persist *doc* under the key *filename* in docs.json.

    If an entry for *filename* already exists it is overwritten; otherwise
    a new key is inserted.  The entire store is rewritten on each call —
    this is intentional given the small, flat-file nature of the storage.

    Args:
        filename: Unique identifier for the document (e.g. ``"README.md"``).
        doc:      Arbitrary dictionary representing the document record.

    Raises:
        OSError: If the file cannot be written to disk.
    """
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("'filename' must be a non-empty string.")
    if not isinstance(doc, dict):
        raise TypeError(f"'doc' must be a dict, got {type(doc).__name__!r}.")

    _ensure_store()
    store = _read_store()
    store[filename] = doc
    _write_store(store)
    logger.debug("Saved doc '%s' to store.", filename)


def get_all_docs() -> dict[str, Any]:
    """Return all document records from docs.json.

    Returns:
        A dictionary mapping each *filename* key to its document dict.
        Returns an empty dict ``{}`` if the store is empty or uninitialised.
    """
    _ensure_store()
    return _read_store()


def get_doc(filename: str) -> dict[str, Any] | None:
    """Retrieve a single document record by *filename*.

    Args:
        filename: The key used when the document was saved.

    Returns:
        The document dict, or ``None`` if no entry exists for *filename*.
    """
    _ensure_store()
    store = _read_store()
    return store.get(filename)
