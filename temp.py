from app.src.services.serper import get_serper_responses
from app.src.services.scrapper import run_scraping_pipeline
from app.src.services.prelim import run_haiku_analysis
import asyncio
from app.src.services.consolidator import run_consolidator
from app.src.services.writer import run_writer

def main():
    responses = get_serper_responses("best productivity tools for remote teams")
    pages = run_scraping_pipeline(responses)
    analyses = asyncio.run(run_haiku_analysis(pages, "best productivity tools for remote teams"))
    blueprint = asyncio.run(run_consolidator(analyses, "best productivity tools for remote teams", 1000))
    written = asyncio.run(run_writer(blueprint, 1000))
    print(written)

if __name__ == "__main__":
    main()