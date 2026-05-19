from pydantic import BaseModel

from ingestion.models import Chunk


class EmbeddedChunk(BaseModel):
    chunk: Chunk
    dense_vector: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]

    model_config = {"arbitrary_types_allowed": True}
