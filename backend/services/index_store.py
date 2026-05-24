import os
import json
import numpy as np
from services.embedder import encode
from services.chunker import chunk_doc

# Try importing faiss
FAISS_AVAILABLE = False
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FAISS not found. Falling back to NumPy-based vector store. Error: {str(e)}")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks.json")

def add_docs(docs) -> None:
    """
    Chunks all documentation, embeds each chunk, and builds a vector index.
    Saves the index and mapping to disk.
    
    docs can be:
      - a dict: {filename: doc_dict}
      - a list of dicts: [doc_dict, doc_dict] where filename is embedded inside
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    
    all_chunks = []
    
    # Robust documentation parsing
    if isinstance(docs, dict):
        for filename, doc in docs.items():
            if isinstance(doc, dict):
                chunks = chunk_doc(filename, doc)
                all_chunks.extend(chunks)
    elif isinstance(docs, list):
        for doc in docs:
            if isinstance(doc, dict):
                filename = doc.get("filename") or doc.get("file") or "unknown_file"
                chunks = chunk_doc(filename, doc)
                all_chunks.extend(chunks)
                
    if not all_chunks:
        print("Warning: No chunks to index.")
        # Create and save an empty index / chunk map
        if FAISS_AVAILABLE:
            index = faiss.IndexFlatIP(384)
            faiss.write_index(index, INDEX_PATH)
        else:
            np.save(INDEX_PATH + ".npy", np.empty((0, 384), dtype=np.float32))
            
        with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    # Extract texts and compute embeddings
    embeddings = []
    for chunk in all_chunks:
        emb = encode(chunk["chunk_text"])
        embeddings.append(emb)
        
    emb_matrix = np.array(embeddings, dtype=np.float32)
    
    # Normalize embeddings for Cosine Similarity (equivalent to inner product on normalized vectors)
    norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    emb_matrix = emb_matrix / norms
    
    # Build vector store index
    if FAISS_AVAILABLE:
        index = faiss.IndexFlatIP(384)
        index.add(emb_matrix)
        faiss.write_index(index, INDEX_PATH)
    else:
        # Fallback to NumPy storage
        np.save(INDEX_PATH + ".npy", emb_matrix)
        
    # Write metadata map
    with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2)
        
    print(f"Successfully indexed {len(all_chunks)} chunks.")

def search(question: str, k: int = 5) -> list[dict]:
    """
    Encodes the question and returns the top-k matching chunks with their source
    filenames and function names.
    """
    if not os.path.exists(CHUNKS_PATH):
        print(f"Warning: Chunk mapping file does not exist at {CHUNKS_PATH}")
        return []
        
    try:
        with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
    except Exception as e:
        print(f"Error loading chunks mapping: {str(e)}")
        return []
        
    if not chunks:
        return []
        
    q_emb = encode(question)
    
    # Normalize question vector
    q_norm = np.linalg.norm(q_emb)
    if q_norm > 0:
        q_emb = q_emb / q_norm
        
    indices = []
    
    # Check if FAISS can search
    if FAISS_AVAILABLE and os.path.exists(INDEX_PATH):
        try:
            index = faiss.read_index(INDEX_PATH)
            q_emb_reshaped = q_emb.reshape(1, -1).astype(np.float32)
            # search takes k, returns distances and indices
            distances, I = index.search(q_emb_reshaped, min(k, len(chunks)))
            indices = I[0].tolist()
        except Exception as e:
            print(f"Error searching FAISS index: {str(e)}. Falling back to NumPy.")
            indices = []
            
    # Fallback to NumPy cosine similarity search if FAISS search wasn't executed/failed
    if not indices:
        npy_path = INDEX_PATH + ".npy"
        if os.path.exists(npy_path):
            try:
                emb_matrix = np.load(npy_path)
                # Compute dot product scores
                scores = np.dot(emb_matrix, q_emb)
                # Sort descending
                indices = np.argsort(scores)[::-1][:min(k, len(chunks))].tolist()
            except Exception as e:
                print(f"Error searching NumPy index: {str(e)}")
                return []
                
    # Retrieve corresponding chunks
    results = []
    for idx in indices:
        if 0 <= idx < len(chunks):
            results.append(chunks[idx])
            
    return results
