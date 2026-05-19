from pydantic import BaseModel


class SearchResult(BaseModel):
    chunk_id: int
    text: str
    score: float
    source: str | None = None
