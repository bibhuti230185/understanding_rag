import hashlib
import re
from pathlib import Path
from uuid import UUID, uuid4

from pypdf import PdfReader


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 160


def extract_pdf_chunks(path: Path) -> list[tuple[UUID, str, int]]:
    reader = PdfReader(str(path), strict=True)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported.")

    chunks: list[tuple[UUID, str, int]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = re.sub(r"\s+", " ", page.extract_text() or "").strip()
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            excerpt = text[start:end].strip()
            if excerpt:
                digest = hashlib.sha256(
                    f"{page_number}:{start}:{excerpt}".encode("utf-8")
                ).hexdigest()
                chunk_id = UUID(digest[:32])
                chunks.append((chunk_id, excerpt, page_number))
            if end == len(text):
                break
            start = end - CHUNK_OVERLAP
    return chunks
