from pydantic import BaseModel
from typing import Optional


class OutboundLink(BaseModel):
    url: str
    anchor_text: str
    context: str


class ScrapedPage(BaseModel):
    url: str
    rank: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: list[str] = []
    body_text: Optional[str] = None
    word_count: int = 0
    outbound_links: list[OutboundLink] = []
    scrape_success: bool = True
    error: Optional[str] = None