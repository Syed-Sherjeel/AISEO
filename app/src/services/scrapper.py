
import trafilatura
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp

from app.src.utils.env import get_firecrawl_api_key

from app.src.models import BaseSerperResponse, ScrapedPage, OutboundLink, SerperResponses

fc_app = FirecrawlApp(api_key=get_firecrawl_api_key()) 



def extract_content(html: str) -> dict:
    body_text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False
    )

    meta = trafilatura.extract_metadata(html)

    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append(f"{tag.name.upper()}: {text}")

    return {
        "title": meta.title if meta else None,
        "meta_description": meta.description if meta else None,
        "headings": headings,
        "body_text": body_text,
        "word_count": len(body_text.split()) if body_text else 0,
    }



def extract_outbound_links(html: str, source_url: str) -> list[OutboundLink]:
    from urllib.parse import urlparse
    source_domain = urlparse(source_url).netloc

    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    links = []

    for p in soup.find_all("p"):
        for a in p.find_all("a", href=True):
            href = a["href"]
            anchor = a.get_text(strip=True)

            if not anchor or not href.startswith("http"):
                continue
            if urlparse(href).netloc == source_domain:
                continue
            if href in seen:
                continue

            seen.add(href)
            links.append(OutboundLink(
                url=href,
                anchor_text=anchor,
                context=p.get_text(strip=True)[:200]
            ))

    return links


def scrape_page(result: BaseSerperResponse, app: FirecrawlApp) -> ScrapedPage:
    try:
        response = app.scrape(
            result.link,
            only_main_content=False,
            max_age=172800000,
            parsers=["pdf"],
            formats=["html"]
        )
        html = response.html
        if not html:
            return ScrapedPage(
                url=result.link,
                rank=result.position,
                scrape_success=False,
                error="Firecrawl returned no HTML"
            )

        outbound_links = extract_outbound_links(html, source_url=result.link)
        content = extract_content(html)

        return ScrapedPage(
            url=result.link,
            rank=result.position,
            outbound_links=outbound_links,
            scrape_success=True,
            **content
        )

    except Exception as e:
        return ScrapedPage(
            url=result.link,
            rank=result.position,
            scrape_success=False,
            error=str(e)
        )
        

def apply_snippet_fallback(
    pages: list[ScrapedPage],
    serper_responses: SerperResponses
) -> list[ScrapedPage]:
    snippet_map = {r.link: r for r in serper_responses.results}

    for page in pages:
        if not page.scrape_success and page.url in snippet_map:
            source = snippet_map[page.url]
            page.body_text = source.snippet
            page.word_count = len(source.snippet.split())
            page.title = source.title

    return pages


def run_scraping_pipeline(
    serper_responses: SerperResponses,
) -> list[ScrapedPage]:
    pages = []

    for result in serper_responses.results:
        print(f"Scraping [{result.position}/10]: {result.link}")
        page = scrape_page(result, fc_app)
        pages.append(page)

    pages = apply_snippet_fallback(pages, serper_responses)

    successful = sum(1 for p in pages if p.scrape_success)
    print(f"Done: {successful}/{len(pages)} succeeded")

    return pages