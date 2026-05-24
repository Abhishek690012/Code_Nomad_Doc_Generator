import numpy as np
import hashlib

model = None
_initialization_attempted = False

def _get_model():
    global model, _initialization_attempted
    if not _initialization_attempted and model is None:
        _initialization_attempted = True
        try:
            print("Loading SentenceTransformer ('all-MiniLM-L6-v2'). This may take a few seconds...")
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            print("SentenceTransformer loaded successfully!")
        except Exception as e:
            print(f"Warning: Could not load SentenceTransformer ('all-MiniLM-L6-v2'). "
                  f"Proceeding in deterministic mock embedding mode. Error: {str(e)}")
    return model

def encode(text: str) -> np.ndarray:
    """
    Encodes the given text string into a 384-dimensional dense vector.
    If sentence-transformers is not available or fails to initialize,
    generates a deterministic 384-dimensional unit vector using sha256.
    """
    current_model = _get_model()
    if current_model is not None:
        try:
            emb = current_model.encode(text)
            # Ensure it is a numpy array
            return np.array(emb, dtype=np.float32)
        except Exception as e:
            print(f"Error encoding with SentenceTransformer: {str(e)}. Falling back to mock.")
            
    # Deterministic fallback: Hash text to initialize a local random number generator,
    # ensuring the same text chunk always yields the exact same mock vector.
    hasher = hashlib.sha256(text.encode('utf-8'))
    seed = int.from_bytes(hasher.digest()[:4], byteorder='big')
    
    rng = np.random.default_rng(seed)
    # Generate 384 dimensions
    mock_vector = rng.standard_normal(384, dtype=np.float32)
    
    # Normalize the vector to unit L2 norm
    norm = np.linalg.norm(mock_vector)
    if norm > 0:
        mock_vector = mock_vector / norm
        
    return mock_vector
