"""Topic similarity detection using embeddings"""

import numpy as np
from sentence_transformers import SentenceTransformer

# Initialize model as None for lazy loading
model = None

def get_embedding(text):
    """Get embedding using sentence-transformers"""
    print("[DEBUG] Using sentence-transformers embedding")
    global model
    if model is None:
        print("[DEBUG] Initializing sentence-transformers model")
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text, convert_to_numpy=True)

def get_similarity_score(text, topics):
    """Calculate similarity score between text and topics"""
    if not text or not topics:
        return 0.0
    
    print("[DEBUG] Calculating similarity score for text against topics:", topics)

    # Get embeddings
    text_embedding = get_embedding(text)
    topic_embeddings = [get_embedding(topic) for topic in topics]

    if text_embedding is None or not topic_embeddings:
        return 0.0

    # Calculate cosine similarity with each topic
    similarities = []
    for topic_embedding in topic_embeddings:
        if topic_embedding is not None:
            similarity = np.dot(text_embedding, topic_embedding) / (
                np.linalg.norm(text_embedding) * np.linalg.norm(topic_embedding)
            )
            similarities.append(similarity)

    return max(similarities) if similarities else 0.0

def check_topic_relevance(text, topics, threshold=0.5):
    """Check if text is relevant to any topic"""
    score = get_similarity_score(text, topics)
    return score >= threshold
