from auth.gmail_auth import get_gmail_service
from services.ingestion.fetch_emails import get_latest_newsletter_text, create_job
from services.ingestion.article_scraper import scrape_article
from db.database import Article
import time

def run_ingestion_loop():
    gmail = get_gmail_service()

    while True:
        texts = get_latest_newsletter_text(gmail, "dan@tldrnewsletter.com")

        for text in texts:
            create_job(
                source_text=text,
                sender="dan@tldrnewsletter.com",
                subject="TLDR Newsletter"
            )
        
        time.sleep(300)

if __name__ == "__main__":
    run_ingestion_loop()