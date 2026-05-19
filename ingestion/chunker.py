import hashlib
import tiktoken

from .models import Chunk, Document

_ENCODING = "cl100k_base"


def _stable_id(doc_source: str, index: int) -> int:
    """64-bit deterministic ID from (doc_source, chunk_index).

    Stable across re-ingests so Qdrant upserts are idempotent, and globally
    unique across documents so multi-file ingestion does not overwrite chunks.
    """
    digest = hashlib.sha256(f"{doc_source}:{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def chunk_documents(
    docs: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    company: str = "",
) -> list[Chunk]:
    enc = tiktoken.get_encoding(_ENCODING)
    chunks: list[Chunk] = []

    # Running chunk index per source — must span all pages so that
    # page 0 chunk 0 and page 1 chunk 0 from the same file get different IDs.
    source_index: dict[str, int] = {}

    for doc in docs:
        tokens = enc.encode(doc.text)
        i = 0
        while i < len(tokens):
            window = tokens[i : i + chunk_size]
            text = enc.decode(window).strip()
            if text:
                idx = source_index.get(doc.source, 0)
                chunks.append(Chunk(
                    doc_source=doc.source,
                    chunk_id=_stable_id(doc.source, idx),
                    text=text,
                    token_count=len(window),
                    company=company,
                ))
                source_index[doc.source] = idx + 1
            i += chunk_size - chunk_overlap

    return chunks
