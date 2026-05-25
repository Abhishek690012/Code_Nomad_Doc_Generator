"""
services/embedder.py
--------------------
Lightweight embedding client for Codewise.

Calls the Hugging Face Serverless Inference API to obtain 384-dimensional
sentence embeddings from the ``all-MiniLM-L6-v2`` model instead of loading
any local ML library (sentence-transformers / PyTorch).

This approach eliminates the heavy memory footprint that was causing OOM
crashes on Render's free-tier (512 MB RAM) instances.

Environment Variables
---------------------
HF_TOKEN : str
    Hugging Face API token with at least ``inference`` permission.
    If absent, a deterministic hash-based mock vector is returned so that
    local development and CI do not require a real token.

Output Shape / Type
-------------------
• encode(str)            → np.ndarray of shape (384,)  dtype float32
• encode(list[str])      → np.ndarray of shape (N, 384) dtype float32

Both outputs are identical in shape/type to what sentence-transformers
previously returned, so index_store.py / query.py need no changes.
"""

import os
import time
import hashlib

import numpy as np
import requests


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HF_API_URL = (
    "https://router.huggingface.co/pipeline/feature-extraction/"
    "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DIM = 384
MAX_RETRIES = 4          # maximum number of attempts including the first
DEFAULT_WAIT = 20.0      # seconds to wait when estimated_time is not provided


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_headers() -> dict:
    """Build the Authorization header from HF_TOKEN, if set."""
    headers = {"Content-Type": "application/json"}
    token = os.getenv("HF_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _hf_request(payload: dict) -> list:
    """
    Send a POST request to the HF Inference API with automatic cold-start
    retry logic.

    HF free models are paused after inactivity. A paused model returns:
        HTTP 503 + JSON body: {"error": "...", "estimated_time": <float>}

    This function detects that condition, sleeps for ``estimated_time``
    seconds, and retries up to MAX_RETRIES times before raising.

    Returns
    -------
    list
        Raw JSON response body from the HF API (a list of embedding arrays).

    Raises
    ------
    RuntimeError
        If all retries are exhausted or an unrecoverable HTTP error occurs.
    """
    headers = _get_headers()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        except requests.exceptions.RequestException as exc:
            # Retry transient network errors (DNS, connection reset, timeout)
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"[Embedder] Network error calling HF API: {exc}") from exc
            wait = DEFAULT_WAIT * attempt
            print(
                f"[Embedder] Network error (attempt {attempt}/{MAX_RETRIES}): {exc}. "
                f"Retrying in {wait:.0f}s..."
            )
            time.sleep(wait)
            continue

        # --- Happy path ---------------------------------------------------
        if response.status_code == 200:
            return response.json()

        # --- Cold-start: model is loading ---------------------------------
        if response.status_code == 503:
            try:
                body = response.json()
            except Exception:
                body = {}
            wait_time = float(body.get("estimated_time", DEFAULT_WAIT))
            print(
                f"[Embedder] HF model is loading (attempt {attempt}/{MAX_RETRIES}). "
                f"Waiting {wait_time:.1f}s before retry..."
            )
            time.sleep(wait_time)
            continue

        # --- Unrecoverable HTTP error -------------------------------------
        raise RuntimeError(
            f"[Embedder] HF API returned HTTP {response.status_code}: {response.text[:300]}"
        )

    raise RuntimeError(
        f"[Embedder] HF API remained unavailable after {MAX_RETRIES} retries."
    )


def _mock_embed(text: str) -> np.ndarray:
    """
    Deterministic 384-dimensional fallback vector derived from the SHA-256
    hash of *text*.  The same input always produces the same unit vector so
    FAISS queries remain consistent in offline / no-token environments.
    """
    hasher = hashlib.sha256(text.encode("utf-8"))
    seed = int.from_bytes(hasher.digest()[:4], byteorder="big")
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode(text: "str | list[str]") -> np.ndarray:
    """
    Encode one or more text strings into dense embedding vectors.

    Parameters
    ----------
    text : str or list[str]
        A single string or a list of strings to embed.

    Returns
    -------
    np.ndarray
        • Shape ``(384,)``     when *text* is a ``str``.
        • Shape ``(N, 384)``   when *text* is a ``list`` of N strings.
        Dtype is always ``float32``.
    """
    is_single = isinstance(text, str)
    inputs = [text] if is_single else list(text)

    token = os.getenv("HF_TOKEN")
    if not token:
        print(
            "[Embedder] Warning: HF_TOKEN not set. "
            "Using deterministic mock embeddings."
        )
        vectors = np.array([_mock_embed(t) for t in inputs], dtype=np.float32)
        return vectors[0] if is_single else vectors

    # --- Live HF API path -------------------------------------------------
    try:
        raw = _hf_request({"inputs": inputs})
    except RuntimeError as exc:
        # Graceful degradation: fall back to mock so the pipeline doesn't crash.
        print(f"[Embedder] Falling back to mock embeddings. Reason: {exc}")
        vectors = np.array([_mock_embed(t) for t in inputs], dtype=np.float32)
        return vectors[0] if is_single else vectors

    # --- Normalise HF response shape -------------------------------------
    # HF returns: list[list[float]]  shape (N, 384)
    # For a single input it is still [[float, ...]] — strip the outer dim.
    arr = np.array(raw, dtype=np.float32)

    # Guard: if for some reason we get shape (1, 384) for a single string,
    # squeeze it down to (384,).
    if is_single:
        arr = arr.squeeze(0) if arr.ndim == 2 else arr

    return arr
