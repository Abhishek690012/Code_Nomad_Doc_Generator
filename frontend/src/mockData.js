export const mockDocs = {
  "src/main.py": {
    summary: "Main entry point for the backend application. Initializes Flask app and routes.",
    functions: [
      {
        name: "initialize_app",
        description: "Sets up the Flask application, loads configurations, and registers blueprints.",
      },
      {
        name: "main",
        description: "Runs the Flask development server on port 5000.",
      },
    ],
  },
  "utils/helpers.py": {
    summary: "Utility functions used across different services, including data formatting and string manipulation.",
    functions: [
      {
        name: "format_date",
        description: "Converts a datetime object into a standardized string format (YYYY-MM-DD).",
      },
      {
        name: "sanitize_input",
        description: "Cleans up user input by removing illegal characters and stripping whitespaces.",
      },
    ],
  },
  "models/user.py": {
    summary: "Defines the User data model and schema for database serialization.",
    functions: [
      {
        name: "User.__init__",
        description: "Initializes a new User instance with username, email, and default role.",
      },
      {
        name: "User.to_dict",
        description: "Serializes the User object into a dictionary for JSON responses.",
      },
    ],
  },
};

export const mockQueryResponse = {
  answer:
    "The authentication is handled in the auth_middleware function using JWTs.",
  source_file: "src/middleware.py",
  function_name: "auth_middleware",
  snippet:
    "def auth_middleware(req):\n    token = req.headers.get('Authorization')\n    return verify_jwt(token)",
};
