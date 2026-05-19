from ingestion.chunker import chunk_documents
from ingestion.models import Document


def _doc(text: str) -> Document:
    return Document(source="test.pdf", page=0, text=text)


def test_single_short_document_produces_one_chunk():
    docs = [_doc("This is a short document with fewer than a thousand tokens.")]
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=150)
    assert len(chunks) == 1
    assert chunks[0].doc_source == "test.pdf"
    assert isinstance(chunks[0].chunk_id, int) and chunks[0].chunk_id > 0


def test_long_document_produces_multiple_chunks():
    # ~2200 tokens of text — should produce 3 chunks at size=1000, overlap=150
    words = ["word"] * 2200
    docs = [_doc(" ".join(words))]
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=150)
    assert len(chunks) >= 2


def test_overlap_produces_shared_tokens():
    words = list(range(1200))
    text = " ".join(str(w) for w in words)
    docs = [_doc(text)]
    chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=200)
    # chunk 1 starts 200 tokens before the end of chunk 0, so the last words
    # of chunk 0 must appear somewhere inside chunk 1 (not necessarily at [:5])
    end_of_first = chunks[0].text.split()[-5:]
    chunk1_words = set(chunks[1].text.split())
    assert any(t in chunk1_words for t in end_of_first)


def test_empty_document_produces_no_chunks():
    docs = [_doc("")]
    chunks = chunk_documents(docs)
    assert chunks == []


def test_chunk_ids_are_unique_across_sources():
    doc_a = Document(source="a.pdf", page=0, text="Content for document A.")
    doc_b = Document(source="b.pdf", page=0, text="Content for document B.")
    chunks = chunk_documents([doc_a, doc_b])
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk IDs must be globally unique"


def test_chunk_ids_are_stable():
    docs = [_doc("Stable content that never changes.")]
    first = chunk_documents(docs)[0].chunk_id
    second = chunk_documents(docs)[0].chunk_id
    assert first == second, "same (source, position) must always yield the same ID"


def test_chunk_token_count_is_set():
    docs = [_doc("Hello world this is a test sentence.")]
    chunks = chunk_documents(docs)
    assert all(c.token_count > 0 for c in chunks)
