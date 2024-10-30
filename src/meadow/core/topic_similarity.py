"""Topic similarity detection using embeddings"""

import numpy as np

# Try to import Apple's NLEmbedding
try:
    from Foundation import NSString
    import NaturalLanguage
    APPLE_EMBEDDINGS = True
except ImportError:
    APPLE_EMBEDDINGS = False
    from sentence_transformers import SentenceTransformer
    model = None

def use_apple_embeddings():
    """Check if Apple embeddings are available"""
    return APPLE_EMBEDDINGS

def get_apple_embedding(text):
    """Get embedding using Apple's NLEmbedding"""
    embedding = NaturalLanguage.NLEmbedding.wordEmbedding()
    if embedding is None:
        return None

    ns_string = NSString.stringWithString_(text)
    vector = embedding.vectorForString_(ns_string)
    if vector is None:
        return None

    return np.array(vector)

def get_fallback_embedding(text):
    """Get embedding using sentence-transformers"""
    global model
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(text, convert_to_numpy=True)

def get_similarity_score(text, topics):
    """Calculate similarity score between text and topics"""
    if not text or not topics:
        return 0.0

    # Get embeddings
    if use_apple_embeddings():
        text_embedding = get_apple_embedding(text)
        topic_embeddings = [get_apple_embedding(topic) for topic in topics]
    else:
        text_embedding = get_fallback_embedding(text)
        topic_embeddings = [get_fallback_embedding(topic) for topic in topics]

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
