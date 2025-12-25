import os
from resume_parser import parse_resume, extract_text_from_pdf
from job_parser import parse_job_description
from scoring import calculate_factor_scores
from database import insert_result
import numpy as np

def format_match_status(score):
    if score == 100:
        return "Matched"
    elif score == 0:
        return "Not Matched"
    else:
        return f"{score}%"


def match_resumes(resume_files, jd_file, user_id):
    """
    Match resumes against a Job Description file, calculate factor scores,
    store results in the database, and return results for display.
    """
    jd_text = extract_text_from_pdf(jd_file)
    jd_parsed = parse_job_description(jd_text)

    results = []

    for rfile in resume_files:
        # Parse resume and calculate factor scores
        resume_parsed = parse_resume(rfile)
        factor_scores = calculate_factor_scores(resume_parsed, jd_parsed)

        # Use name from parsed resume
        resume_name = resume_parsed.get("resume_name", "Unknown Candidate")

        # Format display scores for education & experience
        display_scores = factor_scores.copy()
        display_scores["education"] = format_match_status(factor_scores.get("education", 0))
        display_scores["experience"] = format_match_status(factor_scores.get("experience", 0))

        results.append({
            "resume_name": resume_name,
            "file_name": os.path.basename(rfile),
            "factor_scores": display_scores
        })

        # Safely handle embeddings and any NumPy arrays before DB insertion
        safe_factor_scores = factor_scores.copy()
        for key, value in factor_scores.items():
            if isinstance(value, np.ndarray):
                safe_factor_scores[key] = value.tolist()  # Convert arrays to lists
            elif value is None:
                safe_factor_scores[key] = None
            # Otherwise keep as is

        # Insert into DB
        insert_result(
            user_id=user_id,
            resume_name=resume_name,
            jd_text=jd_text,
            factor_scores=safe_factor_scores
        )

    return results
