# resume_parser.py
import re
import os
import PyPDF2
from nlp_utils import extract_skills, extract_entities


def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text  # ❗ DO NOT lowercase here


def extract_candidate_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()][:15]

    for line in lines:
        lower = line.lower()

        if any(x in lower for x in [
            "resume", "curriculum", "email", "phone",
            "mobile", "linkedin", "github", "@"
        ]):
            continue

        # Mixed case names: Feenaz M. Nargund
        if re.match(r'^([A-Z][a-z]+)(\s[A-Z]\.)?(\s[A-Z][a-z]+)+$', line):
            return line

        # Uppercase names: FEENAZ M NARGUND
        if re.match(r'^[A-Z][A-Z\s\.]{4,}$', line):
            return line.title()

    # 🔹 Smart email fallback
    email_match = re.search(r'([a-zA-Z]+)([._]([a-zA-Z]+))?@', text)
    if email_match:
        first = email_match.group(1)
        last = email_match.group(3)

        if last:
            return f"{first.title()} {last.title()}"
        else:
            return first.title()

    return "Unknown Candidate"




def parse_resume(file_path):
    raw_text = extract_text_from_pdf(file_path)
    text = raw_text.lower()  # lowercased only for NLP

    skills = extract_skills(text)
    entities = extract_entities(text)

    candidate_name = extract_candidate_name(raw_text)

    # Experience in years
    exp_pattern = r'(\d+)(?:\s*-\s*(\d+))?\s+years?'
    matches = re.findall(exp_pattern, text)
    experience_years = max(
        [int(m[1]) if m[1] else int(m[0]) for m in matches],
        default=0
    )

    education = entities.get("DEGREE", []) + entities.get("CERT", [])
    positions = entities.get("POSITION", [])

    return {
        "resume_name": candidate_name,  # ✅ extracted from PDF
        "file_name": os.path.basename(file_path),  # optional
        "text": text,
        "skills": skills,
        "experience": {
            "years": experience_years,
            "positions": positions
        },
        "education": education
    }