import json
from anthropic import AsyncAnthropic

from app.src.models.prelim import PageAnalysis
from app.src.models.consolidator import ContentBlueprint
from app.src.prompts.consolidator import CONSOLIDATOR_SYSTEM_PROMPT
from app.src.utils.env import get_anthropic_api_key

anthropic_client = AsyncAnthropic(api_key=get_anthropic_api_key())

def build_consolidator_message(
    analyses: list[PageAnalysis],
    keyword: str,
    target_word_count: int
) -> str:
    analyses_data = [a.model_dump() for a in analyses]

    return f"""Synthesize the following 10 SEO page analyses into a master content blueprint.\nSERP ANALYSES (ranked 1–10, rank 1 is highest authority):\n{json.dumps(analyses_data, indent=2)}\nTARGET KEYWORD: {keyword}\nTARGET WORD COUNT: {target_word_count}\nProduce the blueprint JSON now."""

async def run_consolidator(
    analyses: list[PageAnalysis],
    keyword: str,
    target_word_count: int,
) -> ContentBlueprint:

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 10000   
        },
        system=[
            {
                "type": "text",
                "text": CONSOLIDATOR_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {
                "role": "user",
                "content": build_consolidator_message(analyses, keyword, target_word_count)
            }
        ]
    )

    raw = next(
        block.text for block in response.content
        if block.type == "text"
    )

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    print(raw)
    parsed = json.loads(raw)
    return ContentBlueprint(keyword=keyword, **parsed)