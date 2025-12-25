# scoring.py
from similarity import calculate_semantic_similarity

def calculate_factor_scores(resume, jd):
    skills_matched = set(resume["skills"]) & set(jd["skills"])
    skills_missing = set(jd["skills"]) - set(resume["skills"])
    skills_score = len(skills_matched) / (len(jd["skills"]) + 1e-6)

    edu_matched = set(resume["education"]) & set(jd["education"])
    edu_score = 1.0 if edu_matched else 0.0

    exp_req = jd["experience"]["years"]
    exp_resume = resume["experience"]["years"]
    exp_score = min(exp_resume / (exp_req + 1e-6), 1.0)

    sem_score, embedding = calculate_semantic_similarity(resume["text"], jd["text"])

    overall_score = 0.4 * skills_score + 0.2 * edu_score + 0.2 * exp_score + 0.2 * sem_score

    return {
        "skills_score": float(skills_score),
        "education_score": float(edu_score),
        "experience_score": float(exp_score),
        "semantic_score": float(sem_score),
        "overall_score": float(overall_score),
        "skills_matched": list(skills_matched),
        "skills_missing": list(skills_missing),
        "embedding": embedding
    }
