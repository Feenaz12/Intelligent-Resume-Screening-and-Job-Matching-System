# database.py
import mysql.connector
import pickle
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------- DB Connection -------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Feenaz@123",
        database="resume_matcher"
    )

# ------------------- Users -------------------
def create_user(username, email, password):
    """Create a new user with hashed password."""
    conn = get_connection()
    cursor = conn.cursor()
    hashed_pw = generate_password_hash(password)
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, email, hashed_pw))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_identifier(identifier):
    """Fetch user by email or username."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE email=%s OR username=%s"
    cursor.execute(query, (identifier, identifier))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def verify_user(identifier, password):
    """Verify credentials using email or username."""
    user = get_user_by_identifier(identifier)
    if user and check_password_hash(user["password"], password):
        return user
    return None

# ------------------- Resume Matching Results -------------------
def insert_result(user_id, resume_name, jd_text, factor_scores):
    """Insert a resume matching result into the DB."""
    if not user_id:
        raise ValueError("user_id must be provided!")

    conn = get_connection()
    cursor = conn.cursor()

    # Normalize factor_scores
    skills_matched = ", ".join(factor_scores.get("skills_matched", []))
    skills_missing = ", ".join(factor_scores.get("skills_missing", []))
    overall_score = float(factor_scores.get("overall_score", 0))
    skills_score = float(factor_scores.get("skills_score", 0))
    education_score = float(factor_scores.get("education_score", 0))
    experience_score = float(factor_scores.get("experience_score", 0))
    semantic_score = float(factor_scores.get("semantic_score", 0))
    embedding_bytes = pickle.dumps(factor_scores.get("embedding")) if factor_scores.get("embedding") else None

    # Prevent duplicates
    cursor.execute("""
        SELECT id FROM match_results
        WHERE user_id=%s AND resume_name=%s AND job_description=%s
    """, (user_id, resume_name, jd_text))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return

    cursor.execute("""
        INSERT INTO match_results
        (user_id, resume_name, job_description, match_score, resume_embedding, skills_matched, skills_missing,
         skills_score, education_score, experience_score, semantic_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        resume_name,
        jd_text,
        overall_score,
        embedding_bytes,
        skills_matched,
        skills_missing,
        skills_score,
        education_score,
        experience_score,
        semantic_score
    ))

    conn.commit()
    cursor.close()
    conn.close()

# ------------------- Fetch History -------------------
def get_user_history(user_id):
    """Fetch all match results for a user, grouped by job_description."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT resume_name, job_description, match_score,
               skills_matched, skills_missing, education_score,
               experience_score, semantic_score
        FROM match_results
        WHERE user_id=%s
        ORDER BY job_description, match_score DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
