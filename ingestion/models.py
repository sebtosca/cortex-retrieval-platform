from pydantic import BaseModel


class Document(BaseModel):
    source: str
    page: int
    text: str


class Chunk(BaseModel):
    doc_source: str
    chunk_id: int
    text: str
    token_count: int = 0
    company: str = ""

    @property
    def metadata(self) -> dict:
        return {"doc_source": self.doc_source, "chunk_id": self.chunk_id}
