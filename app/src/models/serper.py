from pydantic import BaseModel


class BaseSerperResponse(BaseModel):
    title: str
    link: str
    snippet: str
    position: int

class SerperResponses(BaseModel):
    results: list[BaseSerperResponse]
    
    @classmethod
    def from_organic(cls, organic: list) -> "SerperResponses":
        return cls(results=[BaseSerperResponse(**item) for item in organic])
