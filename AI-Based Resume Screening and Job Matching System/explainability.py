from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def get_top_matching_terms(resume_text, job_desc, top_n=5):
    """Return top TF-IDF terms explaining resume-JD match"""
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = vectorizer.fit_transform([resume_text, job_desc])
    
    feature_names = np.array(vectorizer.get_feature_names_out())
    scores = (tfidf[0].toarray() * tfidf[1].toarray()).flatten()
    
    top_indices = scores.argsort()[-top_n:][::-1]
    top_words = feature_names[top_indices]
    return list(top_words)

def get_missing_skills(resume_skills, jd_skills):
    """Return skills present in JD but missing in resume"""
    resume_skills_lower = [s.lower() for s in resume_skills]
    jd_skills_lower = [s.lower() for s in jd_skills]
    return [skill for skill in jd_skills_lower if skill not in resume_skills_lower]
