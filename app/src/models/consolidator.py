from pydantic import BaseModel

class BlueprintSection(BaseModel):
    heading: str                  
    level: str                    
    topics_to_cover: list[str]    
    questions_to_answer: list[str] = []  


class ExternalLinkRecommendation(BaseModel):
    url: str
    anchor_text: str
    relevance: str
    placement_section: str        
    frequency_score: int          

class InternalLinkSuggestion(BaseModel):
    anchor_text: str
    suggested_topic: str         
    placement_section: str      


class SEOMetadata(BaseModel):
    title_tag: str               
    meta_description: str        
    primary_keyword: str
    secondary_keywords: list[str]


class ContentBlueprint(BaseModel):
    keyword: str
    dominant_content_angle: str   
    article_title: str            
    introduction_guidance: str   
    sections: list[BlueprintSection]
    faq_questions: list[str]      
    seo_metadata: SEOMetadata
    external_links: list[ExternalLinkRecommendation]
    internal_links: list[InternalLinkSuggestion]
    content_gaps: list[str]       
    consolidation_reasoning: str 
