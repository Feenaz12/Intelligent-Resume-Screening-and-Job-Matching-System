# similarity.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def calculate_semantic_similarity(resume_text, jd_text):
    embeddings = model.encode([resume_text, jd_text], convert_to_numpy=True)
    score = cosine_similarity(embeddings[0].reshape(1, -1), embeddings[1].reshape(1, -1))[0][0]
    return float(score), embeddings[0]
