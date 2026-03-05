from pydantic import BaseModel

class ArticleSection(BaseModel):
    heading: str
    level: str
    content: str


class FAQItem(BaseModel):
    question: str
    answer: str


class GeneratedArticle(BaseModel):
    title: str
    introduction: str
    sections: list[ArticleSection]
    faq: list[FAQItem]
    conclusion: str
    seo_metadata: dict             # title_tag, meta_description, keywords
    internal_links_used: list[dict]
    external_links_used: list[dict]
    word_count: int