# nlp_utils.py
import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_sm")

# Example predefined skills, can be expanded
DEFAULT_SKILLS = ["python", "java", "ml", "flask", "sql", "spring",
                  "c++", "javascript", "excel", "power bi", "react",
                  "aws", "docker", "html", "css", "ci/cd", "leadership"]

def extract_skills(text, skills_list=DEFAULT_SKILLS):
    text = text.lower()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp(skill) for skill in skills_list]
    matcher.add("SKILLS", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    return list({doc[start:end].text for _, start, end in matches})

def extract_entities(text):
    doc = nlp(text)
    entities = {"POSITION": [], "ORG": [], "CERT": [], "DEGREE": []}
    degrees = ["bachelor", "b.e", "b.tech", "master", "m.tech", "mba", "phd"]
    certs = ["aws certified", "scrum master", "pmp", "google certified"]

    for ent in doc.ents:
        if ent.label_ in ["ORG", "WORK_OF_ART"]:
            entities["ORG"].append(ent.text)
        elif ent.label_ in ["PERSON", "PRODUCT", "LANGUAGE"]:
            entities["POSITION"].append(ent.text)

    # Detect degrees and certifications
    for deg in degrees:
        if deg.lower() in text:
            entities["DEGREE"].append(deg)
    for cert in certs:
        if cert.lower() in text:
            entities["CERT"].append(cert)
    return entities
