import json
from anthropic import AsyncAnthropic

from app.src.prompts.writer import WRITER_SYSTEM_PROMPT
from app.src.models import GeneratedArticle, ContentBlueprint

from app.src.utils.env import get_anthropic_api_key

client = AsyncAnthropic(api_key=get_anthropic_api_key())


def build_writer_message(blueprint: ContentBlueprint, writing_budget: int) -> str:
    return f"Focus on staying under the writing budget for article which following: {writing_budget} This is writing budget for wordcount. Execute the following content blueprint into a complete, publish-ready article.\nBLUEPRINT:\n{json.dumps(blueprint.model_dump(), indent=2)}\nWrite the article now"


async def run_writer(
    blueprint: ContentBlueprint,
    writing_budget: int
) -> GeneratedArticle:
    

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 8000   
        },
        system=[
            {
                "type": "text",
                "text": WRITER_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {
                "role": "user",
                "content": build_writer_message(blueprint, writing_budget)
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

    parsed = json.loads(raw)
    return GeneratedArticle(**parsed)
