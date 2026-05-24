def chunk_doc(filename: str, doc: dict) -> list[dict]:
    """
    Chunks a single file's documentation dictionary into a list of dicts.
    Each output dict has keys:
      - 'chunk_text': plain text representation for embedding search
      - 'source_file': original filename
      - 'function_name': name of the function/class (or 'GLOBAL_SUMMARY')
    """
    chunks = []
    
    summary = doc.get("summary", "")
    language = doc.get("language", "unknown")
    
    # 1. Summary Chunk
    summary_text = (
        f"File: {filename}\n"
        f"Language: {language}\n"
        f"Summary: {summary}"
    )
    chunks.append({
        "chunk_text": summary_text.strip(),
        "source_file": filename,
        "function_name": "GLOBAL_SUMMARY"
    })
    
    # 2. Function Chunks
    for fn in doc.get("functions", []):
        fn_name = fn.get("name", "unknown")
        fn_desc = fn.get("description", "")
        fn_params = fn.get("params", "")
        fn_returns = fn.get("returns", "")
        
        fn_text = (
            f"File: {filename}\n"
            f"Function/Class: {fn_name}\n"
            f"Description: {fn_desc}\n"
            f"Parameters: {fn_params}\n"
            f"Returns: {fn_returns}"
        )
        chunks.append({
            "chunk_text": fn_text.strip(),
            "source_file": filename,
            "function_name": fn_name
        })
        
    return chunks
