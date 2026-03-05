from pydantic import BaseModel
from typing import Optional


class CitedSource(BaseModel):
    url: str
    anchor_text: str
    relevance: str        

class SEOSignals(BaseModel):
    keyword_in_title: bool
    keyword_in_headings: bool
    meta_description_present: bool
    heading_hierarchy_valid: bool  
    estimated_keyword_density: str  

class PageAnalysis(BaseModel):
    url: str
    rank: int
    content_angle: str            
    primary_keyword: str          
    secondary_keywords: list[str]
    topics_covered: list[str]     
    heading_structure: list[str]  
    questions_covered: list[str]  
    cited_sources: list[CitedSource]  
    seo_signals: SEOSignals
    summary: str                  
    analysis_success: bool = True
    error: Optional[str] = None