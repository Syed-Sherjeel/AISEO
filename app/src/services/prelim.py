import json
from anthropic import AsyncAnthropic
from app.src.models import ScrapedPage
from app.src.models.prelim import PageAnalysis, SEOSignals
from app.src.prompts.prelim import SYSTEM_PROMPT
from app.src.utils.env import get_anthropic_api_key

anthropic_client = AsyncAnthropic(api_key=get_anthropic_api_key())


def build_user_message(page: ScrapedPage, keyword: str) -> str:
    page_data = {
        "target_keyword": keyword,
        "rank": page.rank,
        "url": page.url,
        "title": page.title,
        "meta_description": page.meta_description,
        "word_count": page.word_count,
        "headings": page.headings,
        "body_preview": (page.body_text or "")[:3000],
        "outbound_links": [
            l.model_dump() for l in page.outbound_links[:20]
        ]
    }

    return f"""Analyze this page for the target keyword and return the JSON structure defined in your instructions.\nPAGE DATA:\n{json.dumps(page_data, indent=2)}"""


async def analyze_page_with_haiku(
    page: ScrapedPage,
    keyword: str,
) -> PageAnalysis:
    if not page.body_text:
        return PageAnalysis(
            url=page.url,
            rank=page.rank,
            content_angle="unknown",
            primary_keyword=keyword,
            secondary_keywords=[],
            topics_covered=[],
            heading_structure=[],
            questions_covered=[],
            cited_sources=[],
            seo_signals=SEOSignals(
                keyword_in_title=False,
                keyword_in_headings=False,
                meta_description_present=False,
                heading_hierarchy_valid=False,
                estimated_keyword_density="low"
            ),
            summary="Page could not be scraped. No content available for analysis.",
            analysis_success=False,
            error="No body text available"
        )

    try:
        response = await anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}  
                }
            ],
            messages=[
                {"role": "user", "content": build_user_message(page, keyword)}
            ]
        )

        raw = response.content[0].text.strip()

        # strip accidental markdown fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)

        return PageAnalysis(
            url=page.url,
            rank=page.rank,
            **parsed
        )

    except json.JSONDecodeError as e:
        return PageAnalysis(
            url=page.url,
            rank=page.rank,
            content_angle="unknown",
            primary_keyword=keyword,
            secondary_keywords=[],
            topics_covered=[],
            heading_structure=[],
            questions_covered=[],
            cited_sources=[],
            seo_signals=SEOSignals(
                keyword_in_title=False,
                keyword_in_headings=False,
                meta_description_present=False,
                heading_hierarchy_valid=False,
                estimated_keyword_density="low"
            ),
            summary="JSON parsing failed.",
            analysis_success=False,
            error=f"JSON parse error: {str(e)}"
        )

    except Exception as e:
        return PageAnalysis(
            url=page.url,
            rank=page.rank,
            content_angle="unknown",
            primary_keyword=keyword,
            secondary_keywords=[],
            topics_covered=[],
            heading_structure=[],
            questions_covered=[],
            cited_sources=[],
            seo_signals=SEOSignals(
                keyword_in_title=False,
                keyword_in_headings=False,
                meta_description_present=False,
                heading_hierarchy_valid=False,
                estimated_keyword_density="low"
            ),
            summary="Analysis failed.",
            analysis_success=False,
            error=str(e)
        )

async def run_haiku_analysis(
    pages: list[ScrapedPage],
    keyword: str
) -> list[PageAnalysis]:
    
    analyses = []

    for page in pages:
        print(f"Analyzing [{page.rank}/{len(pages)}]: {page.url}")
        analysis = await analyze_page_with_haiku(page, keyword)
        analyses.append(analysis)

    successful = sum(1 for a in analyses if a.analysis_success)
    print(f"Analysis complete: {successful}/{len(analyses)} succeeded")

    return analyses
