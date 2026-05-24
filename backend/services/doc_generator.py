import os
import re
import json
import ast
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert technical writer and AI assistant. Your task is to analyze the provided source code file and generate clear, structured documentation in JSON format.

You must return a valid JSON object ONLY. Do NOT wrap the JSON in markdown code blocks like ```json ... ```. Just return raw JSON.
The JSON object must follow this exact schema:
{
  "summary": "A clean, plain-English summary explaining the file's main purpose, what problem it solves, and how it fits into the application.",
  "language": "The programming language of the file (e.g., 'python', 'javascript', 'typescript', etc.)",
  "functions": [
    {
      "name": "The name of the function, class, or method",
      "description": "A clear explanation of what the function/class does and its logic.",
      "params": "Description of the input parameters, their types, and purposes (e.g., 'repo (str): repository name')",
      "returns": "Description of the return value and type (e.g., 'str: the file content')"
    }
  ]
}

If there are no functions or classes, return an empty list for "functions".
Ensure that all fields are populated accurately based on the source code. Keep description texts concise but informative.
"""

def extract_json(text: str) -> dict:
    """
    Extracts a JSON object from text, handling potential LLM conversational prefixes
    or markdown code fences (```json ... ```).
    """
    text = text.strip()
    
    # Strip markdown wrappers if they exist
    if text.startswith("```"):
        # Remove starting fence, which might be ```json or just ```
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        # Remove ending fence
        text = re.sub(r"\s*```$", "", text)
    
    text = text.strip()
    
    # Find the outer JSON boundaries
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to fix some common LLM JSON syntax errors (like trailing commas)
            # and re-raise if it still fails
            raise ValueError(f"JSON decode failed: {str(e)}. String was: {json_str}")
            
    raise ValueError(f"No JSON object found in response: {text}")

def generate_mock_doc(filename: str, content: str) -> dict:
    """
    Statically analyzes code to generate mock documentation if Groq API key is not present.
    Supports basic AST parsing for Python and regex for Javascript.
    """
    # Detect language by extension
    ext = os.path.splitext(filename)[1].lower()
    language = "unknown"
    functions = []
    
    if ext == '.py':
        language = "python"
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    params = ", ".join([arg.arg for arg in node.args.args])
                    # Try to extract docstring
                    docstring = ast.get_docstring(node) or "No docstring provided."
                    functions.append({
                        "name": node.name,
                        "description": f"Python function: {docstring.strip()}",
                        "params": params if params else "None",
                        "returns": "Undetermined"
                    })
                elif isinstance(node, ast.ClassDef):
                    functions.append({
                        "name": node.name,
                        "description": f"Python class definition. Methods: {[n.name for n in node.body if isinstance(n, ast.FunctionDef)]}",
                        "params": "N/A",
                        "returns": "Class Instance"
                    })
        except Exception:
            # Fallback to regex if parsing fails
            pass
            
    if not functions and ext in ['.js', '.jsx', '.ts', '.tsx']:
        language = "javascript" if 'js' in ext else "typescript"
        # Simple regex for functions
        # matches function name(...) or const name = (...) =>
        fn_pattern = r"(?:function\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>)"
        matches = re.findall(fn_pattern, content)
        for m in matches:
            name = m[0] or m[1]
            if name:
                functions.append({
                    "name": name,
                    "description": "Javascript function detected via static analysis.",
                    "params": "Parsed dynamically",
                    "returns": "Unknown"
                })
                
    # Default fallback if no functions parsed
    if not functions:
        functions = [{
            "name": "sample_function",
            "description": "Fallback mock function representation.",
            "params": "None",
            "returns": "None"
        }]
        
    summary = f"Mock documentation for {filename} (static offline analysis). The file contains source code in {language}."
    
    return {
        "summary": summary,
        "language": language,
        "functions": functions
    }

def generate(filename: str, content: str) -> dict:
    """
    Submits file contents to Groq with a structured prompt, parses JSON documentation.
    Falls back to static parsing if GROQ_API_KEY is not available.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print(f"Warning: GROQ_API_KEY not set. Generating static mock documentation for {filename}.")
        return generate_mock_doc(filename, content)
        
    try:
        client = Groq(api_key=api_key)
        user_message = f"File Path: {filename}\n\nFile Content:\n```\n{content}\n```"
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            # We want strict JSON response format
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content
        return extract_json(response_text)
        
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}. Falling back to mock generator.")
        return generate_mock_doc(filename, content)
