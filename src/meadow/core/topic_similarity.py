"""Topic similarity detection using embeddings"""

import os
# Set tokenizers parallelism before importing any HuggingFace modules
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import asyncio
import re
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer

# Tunable Parameters
# -----------------
# Maximum length of each text chunk for analysis
CHUNK_MAX_LENGTH = 200
# Minimum similarity threshold for a chunk to be considered relevant (0.0 to 1.0)
CHUNK_SIMILARITY_THRESHOLD = 0.2
# Minimum number of relevant chunks needed for a topic to be considered matched
MIN_CHUNKS_PER_TOPIC = 3

# Initialize model and cache as None for lazy loading
model = None
model_init_lock = asyncio.Lock()
topic_embedding_cache = {}

def split_into_chunks(text, max_length=CHUNK_MAX_LENGTH):
    """Split text into chunks, preserving sentence boundaries"""
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        # Skip empty sentences
        if not sentence.strip():
            continue

        # If this sentence would exceed max_length and we have content,
        # save current chunk and start new one
        if current_length + len(sentence) > max_length and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0

        # Handle very long sentences by splitting on commas if needed
        if len(sentence) > max_length:
            parts = sentence.split(', ')
            for part in parts:
                if current_length + len(part) > max_length and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(part)
                current_length += len(part)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence)

    # Add any remaining content
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    # Filter out very short chunks
    chunks = [chunk for chunk in chunks if len(chunk.split()) > 5]

    return chunks

async def initialize_model():
    """Explicitly initialize the model"""
    global model
    async with model_init_lock:
        if model is None:
            print("[DEBUG] Initializing sentence-transformers model")
            # Run model initialization in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(None, lambda: SentenceTransformer('all-MiniLM-L6-v2'))
    return model

async def get_embedding(text):
    """Get embedding using sentence-transformers"""
    global model
    if model is None:
        await initialize_model()
    # Run encoding in a thread to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: model.encode(text, convert_to_numpy=True))

async def calculate_similarity(text_embedding, topic_embedding):
    """Calculate cosine similarity between two embeddings"""
    similarity = np.dot(text_embedding, topic_embedding) / (
        np.linalg.norm(text_embedding) * np.linalg.norm(topic_embedding)
    )
    return float(similarity)  # Convert to float for better debug printing

async def get_similarity_score(text, topics, chunk_threshold=CHUNK_SIMILARITY_THRESHOLD, min_chunks=MIN_CHUNKS_PER_TOPIC):
    """Calculate similarity score between text and topics"""
    if not text or not topics:
        return 0.0

    # Split text into chunks for more granular comparison
    chunks = split_into_chunks(text)
    print(f"[DEBUG] Split text into {len(chunks)} chunks")
    print("\n[DEBUG] Chunks:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk[:100]}...")

    # Get embeddings for all chunks
    chunk_embeddings = []
    for chunk in chunks:
        chunk_embedding = await get_embedding(chunk)
        chunk_embeddings.append((chunk, chunk_embedding))

    # Get topic embeddings, using cache when available
    topic_embeddings = []
    for topic in topics:
        if topic not in topic_embedding_cache:
            topic_embedding_cache[topic] = await get_embedding(topic)
        topic_embeddings.append((topic, topic_embedding_cache[topic]))

    # Track chunks that exceed threshold for each topic
    relevant_chunks_by_topic = defaultdict(list)
    max_similarity = 0.0

    # Calculate similarities and group by topic
    for chunk, chunk_embedding in chunk_embeddings:
        for topic, topic_embedding in topic_embeddings:
            similarity = await calculate_similarity(chunk_embedding, topic_embedding)
            print(f"[DEBUG] Similarity between chunk '{chunk[:50]}...' and topic '{topic}': {similarity:.3f}")

            if similarity > chunk_threshold:
                relevant_chunks_by_topic[topic].append({
                    'chunk': chunk,
                    'similarity': similarity
                })
                max_similarity = max(max_similarity, similarity)

    # Print debug info about relevant chunks per topic
    print("\n[DEBUG] Relevant chunks by topic:")
    relevant_topics = []
    for topic, chunks in relevant_chunks_by_topic.items():
        chunks.sort(key=lambda x: x['similarity'], reverse=True)
        print(f"\n[DEBUG] Topic: '{topic}' - {len(chunks)} relevant chunks")

        if len(chunks) >= min_chunks:
            relevant_topics.append(topic)
            print(f"[DEBUG] Topic '{topic}' meets minimum chunk requirement ({min_chunks})")
            for i, chunk_info in enumerate(chunks[:min_chunks]):  # Show top chunks
                print(f"  Chunk {i+1}:")
                print(f"    Similarity: {chunk_info['similarity']:.3f}")
                print(f"    Text: '{chunk_info['chunk'][:100]}...'")
        else:
            print(f"[DEBUG] Topic '{topic}' has insufficient chunks ({len(chunks)} < {min_chunks})")

    # Return max similarity only if any topic has enough relevant chunks
    if relevant_topics:
        print(f"\n[DEBUG] Found {len(relevant_topics)} relevant topics: {relevant_topics}")
        print(f"[DEBUG] Highest similarity score: {max_similarity:.3f}")
        return max_similarity
    else:
        print("\n[DEBUG] No topics had enough relevant chunks")
        return 0.0

async def check_topic_relevance(text, topics, threshold=CHUNK_SIMILARITY_THRESHOLD, min_chunks=MIN_CHUNKS_PER_TOPIC):
    """Check if text is relevant to any topic"""
    score = await get_similarity_score(text, topics, threshold, min_chunks)
    print(f"[DEBUG] Final relevance score: {score:.3f} (threshold: {threshold}, required chunks per topic: {min_chunks})")
    return score >= threshold
