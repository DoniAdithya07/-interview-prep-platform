from io import BytesIO

from fastapi import HTTPException, UploadFile, status

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

SUPPORTED_RESUME_TYPES = {
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_RESUME_BYTES = 3 * 1024 * 1024


async def extract_resume_text(upload: UploadFile) -> str:
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume filename is required")

    content = await upload.read()
    await upload.close()

    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file is empty")
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file is too large")

    content_type = upload.content_type or ""
    filename = upload.filename.lower()
    if content_type not in SUPPORTED_RESUME_TYPES and not filename.endswith((".txt", ".pdf")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume format. Use PDF, DOCX, or TXT.",
        )

    if content_type == "application/pdf" or filename.endswith(".pdf"):
        if PdfReader is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PDF resume support is unavailable on the server.",
            )
        reader = PdfReader(BytesIO(content))
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif content_type.endswith("document.wordprocessingml.document") or filename.endswith(".docx"):
        if Document is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DOCX resume support is unavailable on the server.",
            )
        document = Document(BytesIO(content))
        extracted = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        extracted = content.decode("utf-8", errors="ignore")

    normalized = " ".join(extracted.split())
    if len(normalized) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text could not be extracted. Try a clearer PDF or a TXT file.",
        )
    return normalized[:12000]


def fallback_resume_insights(resume_text: str) -> list[str]:
    chunks = [chunk.strip(" -") for chunk in resume_text.replace(".", "\n").split("\n")]
    insights = [chunk for chunk in chunks if 20 <= len(chunk) <= 120][:3]
    if insights:
        return insights
    return ["Question targeted to the resume's most visible projects and skills."]
