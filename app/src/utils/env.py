import os



def get_serper_api_key() -> str:
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        raise ValueError("SERPER_API_KEY is not set")
    return serper_api_key

def get_firecrawl_api_key() -> str:
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_api_key:
        raise ValueError("FIRECRAWL_API_KEY is not set")
    return firecrawl_api_key

def get_anthropic_api_key() -> str:
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")
    return anthropic_api_key