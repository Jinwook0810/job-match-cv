from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _extract_from_txt(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unsupported text encoding for TXT resume")


def _extract_from_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("PDF parsing support is not installed. Install pypdf to enable PDF resumes.") from e

    reader = PdfReader(BytesIO(content))
    return "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()


def _extract_from_docx(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError as e:
        raise RuntimeError("DOCX parsing support is not installed. Install python-docx to enable DOCX resumes.") from e

    document = Document(BytesIO(content))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs).strip()


async def extract_text_from_upload(upload: UploadFile) -> str:
    filename = upload.filename or "resume"
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only PDF, DOCX, and TXT resumes are supported")

    content = await upload.read()
    if not content:
        raise ValueError("Uploaded resume is empty")

    if suffix == ".txt":
        return _extract_from_txt(content)
    if suffix == ".pdf":
        return _extract_from_pdf(content)
    if suffix == ".docx":
        return _extract_from_docx(content)

    raise ValueError("Unsupported resume format")
