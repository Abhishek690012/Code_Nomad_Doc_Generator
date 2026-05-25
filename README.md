# Code Nomad Doc Generator

This repository contains the Code Nomad Doc Generator project, comprising a web application with a `frontend` and a `backend`.

## Deployment and Hosting Note

These folders are currently uploaded to temporary servers:
- **Frontend** is hosted on **Netlify**.
- **Backend** is hosted on **Render**.

> **Important:** The `frontend` and `backend` subfolders are supposed to go in a separate repository to be hosted there permanently.

## Database
There is **no persistent database** for now. Any data or context is ephemeral and stored in memory or local files temporarily during processing.

---

## Webhook Configuration

To allow the application to track changes in a specific repository and automatically update its documentation context, you need to configure a webhook in that GitHub repository:

1. Go to your target GitHub repository.
2. Navigate to **Settings** > **Webhooks**.
3. Click on **Add webhook**.
4. Set the **Payload URL** to your backend's webhook endpoint (e.g., `https://your-backend-url.onrender.com/webhook`).
5. Set the **Content type** to `application/json`.
6. (Optional but recommended) Set a **Secret** and ensure it matches the `WEBHOOK_SECRET` in your backend environment variables.
7. Choose the events that trigger the webhook. Typically, you want to select **Let me select individual events** and check **Pushes**.
8. Ensure **Active** is checked and click **Add webhook**.

---

## Getting Started Locally

1. Create a `.env` file based on `.env.example` in both the root/backend and frontend as needed.
2. Install Python backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Navigate to `frontend` and install node modules, then run the dev server.
