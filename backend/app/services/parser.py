from pathlib import Path
from pypdf import PdfReader
from docx import Document
from io import BytesIO

def extract_resume_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        doc = Document(BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
    elif ext == ".txt":
        text = content.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")
    text = text.strip()
    if len(text) < 30:
        raise ValueError("Could not extract enough text. Try a text-based PDF or DOCX.")
    return text[:50000]
