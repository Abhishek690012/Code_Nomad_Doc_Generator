import os
import sys
import numpy as np

# Adjust sys.path to enable imports of the services directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import doc_generator, embedder, chunker, index_store, rag

MOCK_FILE_CONTENT = """# auth.py
# A module to verify JWT tokens and generate new sessions.

def verify_token(token: str) -> dict:
    \"\"\"
    Verifies the signature of the incoming JWT token.
    Params:
        token: a base64 encoded JWT string.
    Returns:
        dict: containing user identity claims if valid.
    \"\"\"
    if not token:
        raise ValueError("Token cannot be empty")
    return {"user_id": 42, "role": "admin"}

class SessionManager:
    \"\"\"
    Manages active user sessions.
    \"\"\"
    def __init__(self, db_conn):
        self.db = db_conn
        
    def create_session(self, user_id: int) -> str:
        \"\"\"
        Creates a new session token in the database.
        \"\"\"
        return f"sess_token_{user_id}"
"""

def test_pipeline():
    print("==================================================")
    print("STARTING ROLE A SERVICE ISOLATION TESTS")
    print("==================================================\n")
    
    # 1. Test Doc Generator
    print("--- 1. Testing doc_generator.py ---")
    doc = doc_generator.generate("auth.py", MOCK_FILE_CONTENT)
    print(f"Doc keys: {list(doc.keys())}")
    print(f"Summary: {doc.get('summary')}")
    print(f"Language: {doc.get('language')}")
    print("Functions documented:")
    for f in doc.get("functions", []):
        print(f"  - {f.get('name')}: {f.get('description')} (Params: {f.get('params')}, Returns: {f.get('returns')})")
    print("Doc Generator Test: PASS\n")
    
    # 2. Test Embedder
    print("--- 2. Testing embedder.py ---")
    emb = embedder.encode("Test string to embed")
    print(f"Vector type: {type(emb)}")
    print(f"Vector shape: {emb.shape}")
    assert emb.shape == (384,), f"Expected shape (384,), got {emb.shape}"
    # Verify normalization
    norm = np.linalg.norm(emb)
    print(f"Vector L2 Norm: {norm:.4f}")
    assert np.isclose(norm, 1.0, atol=1e-4), "Vector is not properly normalized!"
    print("Embedder Test: PASS\n")
    
    # 3. Test Chunker
    print("--- 3. Testing chunker.py ---")
    chunks = chunker.chunk_doc("auth.py", doc)
    print(f"Number of chunks created: {len(chunks)}")
    for idx, c in enumerate(chunks):
        print(f"  Chunk {idx + 1}: Source={c.get('source_file')}, Fn={c.get('function_name')}")
        print(f"  Content snippet:\n---\n{c.get('chunk_text')}\n---")
    print("Chunker Test: PASS\n")
    
    # 4. Test Index Store (Save)
    print("--- 4. Testing index_store.py (Save) ---")
    # Clean old files if present
    for path in [index_store.INDEX_PATH, index_store.INDEX_PATH + ".npy", index_store.CHUNKS_PATH]:
        if os.path.exists(path):
            os.remove(path)
            
    # Index our mock docs
    docs_to_index = {"auth.py": doc}
    index_store.add_docs(docs_to_index)
    
    # Verify file persistence
    has_index = os.path.exists(index_store.INDEX_PATH) or os.path.exists(index_store.INDEX_PATH + ".npy")
    has_chunks = os.path.exists(index_store.CHUNKS_PATH)
    print(f"Index file exists: {has_index}")
    print(f"Chunks map file exists: {has_chunks}")
    assert has_index and has_chunks, "Index or chunks mapping files were not created!"
    print("Index Store Save Test: PASS\n")
    
    # 5. Test Index Store (Search)
    print("--- 5. Testing index_store.py (Search) ---")
    search_query = "how to verify security JWT tokens?"
    matches = index_store.search(search_query, k=2)
    print(f"Search Query: '{search_query}'")
    print(f"Matches found: {len(matches)}")
    for idx, match in enumerate(matches):
        print(f"  Match {idx + 1}: Source={match.get('source_file')}, Fn={match.get('function_name')}")
        print(f"  Excerpt: {match.get('chunk_text')[:100]}...")
    assert len(matches) > 0, "No chunks returned from search query!"
    print("Index Store Search Test: PASS\n")
    
    # 6. Test RAG Q&A
    print("--- 6. Testing rag.py ---")
    qa_query = "How do I check if a token is valid, and what does it return?"
    answer_dict = rag.answer(qa_query)
    print(f"Query: '{qa_query}'")
    print(f"Answer dict keys: {list(answer_dict.keys())}")
    print(f"Answer: {answer_dict.get('answer')}")
    print(f"Source file: {answer_dict.get('source_file')}")
    print(f"Function cited: {answer_dict.get('function_name')}")
    print(f"Excerpt snippet: {answer_dict.get('snippet')}")
    
    # Assert return structure
    for key in ["answer", "source_file", "function_name", "snippet"]:
        assert key in answer_dict, f"Missing key '{key}' in RAG answer!"
        
    print("RAG Test: PASS\n")
    
    print("==================================================")
    print("ALL ISOLATION TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_pipeline()
