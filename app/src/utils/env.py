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