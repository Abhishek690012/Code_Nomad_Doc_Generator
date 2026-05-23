"""
services/github_client.py
--------------------------
GitHub REST API client for Codewise.

Provides a function to fetch raw file content from a GitHub repository,
handling Base64 decoding, authorization via GITHUB_TOKEN, and clear
error reporting for common failure cases.
"""

import os
import base64
import requests


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class GitHubClientError(Exception):
    """Base exception for all GitHub client errors."""


class FileNotFoundError(GitHubClientError):
    """Raised when the requested file does not exist in the repository."""


class RateLimitExceededError(GitHubClientError):
    """Raised when the GitHub API rate limit has been hit."""


class GitHubAPIError(GitHubClientError):
    """Raised for unexpected GitHub API response statuses."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT = 10  # seconds


# ---------------------------------------------------------------------------
# Core Function
# ---------------------------------------------------------------------------

def fetch_file_content(repo_name: str, filepath: str) -> str:
    """Fetch and decode the content of a file from a GitHub repository.

    Uses the GitHub Contents API:
      GET /repos/{repo_name}/contents/{filepath}

    The response payload contains the file content encoded in Base64.
    This function decodes it and returns a plain-text string.

    Args:
        repo_name: Full repository name in ``owner/repo`` format
                   (e.g. ``"octocat/Hello-World"``).
        filepath:  Path to the file inside the repository
                   (e.g. ``"src/main.py"``).

    Returns:
        The decoded UTF-8 text content of the requested file.
            
    Raises:
        FileNotFoundError:      The file does not exist at the given path.
        RateLimitExceededError: The GitHub API rate limit has been exhausted.
        GitHubAPIError:         Any other non-2xx response from the API.
        GitHubClientError:      Network-level or unexpected errors.
    """
    token = os.getenv("GITHUB_TOKEN")

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API_BASE}/repos/{repo_name}/contents/{filepath}"

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout as exc:
        raise GitHubClientError(
            f"Request to GitHub API timed out after {REQUEST_TIMEOUT}s."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise GitHubClientError(
            "Failed to connect to the GitHub API. Check network connectivity."
        ) from exc

    # -- Status code handling -----------------------------------------------
    if response.status_code == 404:
        raise FileNotFoundError(
            f"File '{filepath}' not found in repository '{repo_name}'. "
            "Verify the path and that the repository is accessible."
        )

    if response.status_code == 403:
        # GitHub uses 403 for both auth failures and rate-limit exhaustion.
        remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
        if remaining == "0":
            reset_ts = response.headers.get("X-RateLimit-Reset", "unknown")
            raise RateLimitExceededError(
                f"GitHub API rate limit exceeded. Resets at Unix timestamp: {reset_ts}."
            )
        raise GitHubAPIError(
            "Access forbidden (403). Ensure GITHUB_TOKEN has the required scopes."
        )

    if response.status_code == 401:
        raise GitHubAPIError(
            "Authentication failed (401). Verify that GITHUB_TOKEN is valid."
        )

    if not response.ok:
        raise GitHubAPIError(
            f"Unexpected GitHub API response: {response.status_code} — {response.text[:200]}"
        )

    # -- Decode content ------------------------------------------------------
    payload = response.json()

    if isinstance(payload, list):
        # The path points to a directory, not a file.
        raise GitHubClientError(
            f"'{filepath}' is a directory, not a file. Provide a path to a specific file."
        )

    encoding = payload.get("encoding")
    if encoding != "base64":
        raise GitHubClientError(
            f"Unsupported encoding returned by GitHub API: '{encoding}'. Expected 'base64'."
        )

    raw_content = payload.get("content", "")
    # GitHub may include newlines inside the Base64 string; strip them before decoding.
    decoded_bytes = base64.b64decode(raw_content.replace("\n", ""))
    return decoded_bytes.decode("utf-8")
