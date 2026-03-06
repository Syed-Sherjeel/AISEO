from pydantic import BaseModel


class JobRequest(BaseModel):
    query: str
    word_count: int = 1000

class JobResponse(BaseModel):
    id: str
    query: str
    word_count: int
    status: str
    error: str | None = None
    created_at: str
    updated_at: str