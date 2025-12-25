import PyPDF2
import re

def extract_text_from_pdf(file_path):
    """Extract all text from a PDF file"""
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_job_title(file_path):
    """
    Extract the Job Title from a JD PDF.
    Handles multi-line titles until the next section keyword like Responsibilities, Required Skills, Education, or Experience.
    """
    text = extract_text_from_pdf(file_path)
    
    # Use regex with DOTALL to capture multi-line until next section
    match = re.search(
        r'Job\s*Title\s*:\s*(.+?)(?=\n(?:Responsibilities|Required Skills|Education|Experience)\s*:)',
        text, 
        re.IGNORECASE | re.DOTALL
    )
    if match:
        # Clean whitespace and line breaks
        title = match.group(1).replace('\n', ' ').strip()
        return title
    
    # Fallback: first non-empty line
    for line in text.split("\n"):
        if line.strip():
            return line.strip()
    
    return "Job Description"

def extract_job_title_from_text(text):
    """Extract job title from pasted JD text, supports multi-line titles"""
    match = re.search(
        r'Job\s*Title\s*:\s*(.+?)(?=\n(?:Responsibilities|Required Skills|Education|Experience)\s*:)',
        text, 
        re.IGNORECASE | re.DOTALL
    )
    if match:
        title = match.group(1).replace('\n', ' ').strip()
        return title
    
    for line in text.split("\n"):
        if line.strip():
            return line.strip()
    
    return "Pasted Job Description"
