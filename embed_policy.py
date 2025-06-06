import ollama
import numpy as np

def embed_policy_text(text_list):

    try:
        embeddings = []
        for text in text_list:
            response = ollama.embeddings(model='nomic-embed-text', prompt=text)
            embedding = response['embedding']
            print(f"[DEBUG] Embedding dimension: {len(embedding)}")  # Optional debug
            embeddings.append(embedding)
        return np.array(embeddings)
    except Exception as e:
        raise Exception(f"Embedding generation failed: {e}")
