# job_parser.py
from nlp_utils import extract_skills, extract_entities

def parse_job_description(text):
    text = text.lower()
    skills = extract_skills(text)
    entities = extract_entities(text)

    # Experience in years
    import re
    exp_pattern = r'(\d+)(?:\s*-\s*(\d+))?\s+years?'
    matches = re.findall(exp_pattern, text)
    experience_years = max([int(m[1]) if m[1] else int(m[0]) for m in matches], default=0)

    education = entities["DEGREE"] + entities["CERT"]

    return {
        "skills": skills,
        "experience": {"years": experience_years},
        "education": education,
        "text": text
    }
