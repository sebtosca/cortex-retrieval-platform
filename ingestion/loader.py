from pathlib import Path

from .models import Document


def load_pdf(path: Path) -> list[Document]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    docs = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            docs.append(Document(source=path.name, page=page_num, text=text))
    return docs
