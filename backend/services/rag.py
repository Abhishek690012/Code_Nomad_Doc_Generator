import os
import json
from groq import Groq
from dotenv import load_dotenv
import services.index_store as index_store
from services.doc_generator import extract_json

load_dotenv()

RAG_SYSTEM_PROMPT = """You are an expert technical assistant and documentation explorer. Your task is to answer the user's question about the codebase using ONLY the provided documentation context chunks.

You must answer the question based strictly on the provided context. If the answer cannot be found in the context, state "I cannot find the answer in the provided documentation" in the answer field, and return null or empty strings for source_file, function_name, and snippet.

You must return a valid JSON object ONLY. Do NOT wrap the JSON in markdown code blocks like ```json ... ```. Just return raw JSON.
The JSON object must follow this exact schema:
{
  "answer": "A concise, clear, and comprehensive answer to the user's question.",
  "source_file": "The filename (e.g., 'auth.py') of the documentation chunk that most directly contains the answer.",
  "function_name": "The name of the function, class, or method (e.g., 'verify_token') that handles this behavior. Use 'GLOBAL_SUMMARY' if the information is from a file's summary chunk.",
  "snippet": "A short, relevant snippet of the documentation chunk text or code description that contains the source evidence."
}
"""

def generate_mock_answer(question: str, top_chunks: list[dict]) -> dict:
    """
    Generates a structured mock answer if Groq API is offline or not configured.
    Uses the top search match for source attribution.
    """
    if not top_chunks:
        return {
            "answer": "No codebase documentation has been indexed yet. Please run a manual trigger or push files first.",
            "source_file": "",
            "function_name": "",
            "snippet": ""
        }
        
    top = top_chunks[0]
    source_file = top.get("source_file", "unknown")
    function_name = top.get("function_name", "GLOBAL_SUMMARY")
    snippet = top.get("chunk_text", "")
    
    answer_text = (
        f"This is a mock offline answer for your question: '{question}'. "
        f"Based on the most relevant index match in '{source_file}', the logic relates to '{function_name}'. "
        f"Please configure your 'GROQ_API_KEY' to enable synthesized natural language answers."
    )
    
    return {
        "answer": answer_text,
        "source_file": source_file,
        "function_name": function_name,
        "snippet": snippet
    }

def answer(question: str) -> dict:
    """
    Performs vector search, constructs context, calls Groq LLM, and parses response.
    Returns: {answer, source_file, function_name, snippet}
    """
    # 1. Retrieve the top 5 matches from index_store
    top_chunks = index_store.search(question, k=5)
    
    # 2. Check if Groq API key is available
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY not set. Generating mock answer from retrieved context chunks.")
        return generate_mock_answer(question, top_chunks)
        
    if not top_chunks:
        return {
            "answer": "I could not find any relevant documentation to answer this question. Please ensure you have indexed files first.",
            "source_file": "",
            "function_name": "",
            "snippet": ""
        }
        
    try:
        client = Groq(api_key=api_key)
        
        # Format the context chunks for the prompt
        context_lines = []
        for idx, chunk in enumerate(top_chunks):
            context_lines.append(
                f"--- Chunk {idx + 1} ---\n"
                f"File: {chunk.get('source_file', 'unknown')}\n"
                f"Function/Class: {chunk.get('function_name', 'GLOBAL_SUMMARY')}\n"
                f"Documentation:\n{chunk.get('chunk_text', '')}\n"
            )
        context_str = "\n".join(context_lines)
        
        user_message = f"DOCUMENTATION CONTEXT:\n{context_str}\n\nUSER QUESTION: {question}"
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": RAG_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        response_text = chat_completion.choices[0].message.content
        result = extract_json(response_text)
        
        # Ensure all required keys exist in result
        for key in ["answer", "source_file", "function_name", "snippet"]:
            if key not in result:
                result[key] = ""
                
        return result
        
    except Exception as e:
        print(f"Error executing RAG Q&A: {str(e)}. Falling back to mock answer.")
        return generate_mock_answer(question, top_chunks)
