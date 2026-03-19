from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    # Supports long research briefs/prompts (multi-page input).
    query: str = Field(..., min_length=3, max_length=100000)
    limit: int = Field(default=5, ge=1, le=20)


class Lead(BaseModel):
    name: str
    website: str | None = None
    summary: str
    source: str


class ScrapeResponse(BaseModel):
    query: str
    provider: str
    leads: list[Lead]
