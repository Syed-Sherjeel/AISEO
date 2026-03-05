from pydantic import BaseModel
from typing import Optional


class CitedSource(BaseModel):
    url: str
    anchor_text: str
    relevance: str        # why this source was cited in context of the topic


class SEOSignals(BaseModel):
    keyword_in_title: bool
    keyword_in_headings: bool
    meta_description_present: bool
    heading_hierarchy_valid: bool  # h1 → h2 → h3 order respected
    estimated_keyword_density: str  # low / medium / high


class PageAnalysis(BaseModel):
    url: str
    rank: int
    content_angle: str            # listicle / deep-dive / comparison / beginner-guide / case-study
    primary_keyword: str          # what this page seems to be targeting
    secondary_keywords: list[str]
    topics_covered: list[str]     # main subtopics the article addresses
    heading_structure: list[str]  # cleaned h1/h2/h3 list
    questions_covered: list[str]  # any questions the article answers (good for FAQ)
    cited_sources: list[CitedSource]  # filtered outbound links with relevance
    seo_signals: SEOSignals
    summary: str                  # 2-3 sentence summary of why this page ranks
    analysis_success: bool = True
    error: Optional[str] = None