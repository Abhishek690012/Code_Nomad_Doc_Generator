import os
import hmac
import hashlib
from flask import Blueprint, request, jsonify

from services.github_client import fetch_file_content
from services import doc_generator, index_store
from models.doc_store import save_doc, get_all_docs

webhook_bp = Blueprint("webhook_bp", __name__)

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Signature Validation
        signature_header = request.headers.get("X-Hub-Signature-256")
        if not signature_header:
            return jsonify({"error": "Missing signature"}), 403

        secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if not secret:
            return jsonify({"error": "Webhook secret not configured"}), 500

        # Compute HMAC SHA-256 signature of the raw request body
        payload_body = request.get_data()
        hash_object = hmac.new(secret.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
        expected_signature = "sha256=" + hash_object.hexdigest()

        if not hmac.compare_digest(expected_signature, signature_header):
            return jsonify({"error": "Invalid signature"}), 403

        # Event Handling
        github_event = request.headers.get("X-GitHub-Event")
        if github_event == "ping":
            return jsonify({"message": "Ping received"}), 200

        if github_event == "push":
            payload = request.get_json()
            if not payload:
                return jsonify({"error": "Invalid JSON payload"}), 400

            repo_full_name = payload.get("repository", {}).get("full_name")
            if not repo_full_name:
                return jsonify({"error": "Repository name missing"}), 400

            # Collect unique modified/added files
            files_to_process = set()
            commits = payload.get("commits", [])
            for commit in commits:
                for file_path in commit.get("added", []):
                    files_to_process.add(file_path)
                for file_path in commit.get("modified", []):
                    files_to_process.add(file_path)

            processed_files = []
            for file_path in files_to_process:
                # Core pipeline: fetch content, generate docs, and save
                content = fetch_file_content(repo_full_name, file_path)
                if content:
                    doc = doc_generator.generate(file_path, content)
                    save_doc(file_path, doc)
                    processed_files.append(file_path)

            # Rebuild index
            all_docs = get_all_docs()
            index_store.add_docs(all_docs)

            return jsonify({
                "status": "success",
                "files_processed": processed_files
            }), 200

        return jsonify({"message": f"Event {github_event} ignored"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
