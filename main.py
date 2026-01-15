import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pathlib import Path
from typing import List
from bson import ObjectId

from auth.gmail_auth import get_gmail_service
from services.ingestion.fetch_emails import get_latest_newsletter_text
from services.ingestion.article_scraper import scrape_article, get_latest_newsletter_links

from db import db
from db.database import Episode, Article, Text
from processing.script_generator import generate_script, load_model

PROJECT_ROOT = Path(__file__).resolve().parent
CLIENT_SECRET_FILE = PROJECT_ROOT / 'credentials' / 'gmail_oauth.json'

app = FastAPI(title="Podcast Script Generator API")

class ScriptRequest(BaseModel):
    source_text: str
    episode_id: str
    max_tokens: int = 2048

class ScriptResponse(BaseModel):
    episode_id: str
    script: str

model, tokenizer = load_model()

@app.post("/generate_script")
def generate_script_endpoint(req: ScriptRequest):
    '''API endpoint to generate script'''
    try:
        script = generate_script(req.source_text, model, tokenizer)
        return ScriptResponse(
            episode_id=req.episode_id,
            script=script
        )
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Works
def fetch_links() -> List[str]:
    gmail_service = get_gmail_service()
    newsletter_links = get_latest_newsletter_links(gmail_service, 'dan@tldrnewsletter.com')
    return newsletter_links

# Works
def fetch_text() -> List[str]:
    gmail_service = get_gmail_service()
    texts = get_latest_newsletter_text(gmail_service, 'dan@tldrnewsletter.com')
    return texts

# Works
def process_links(links: List[str], episode_name: str, episode_num: int) -> ObjectId:
    print('Creating/accessing episode...')
    episode = Episode(episode_name=episode_name, episode_num=episode_num)
    episode.save()
    print('Episode created and saved.')
    episode_id = episode._id
    print(f'Going through {len(links)} articles.')
    i = 1
    for link in links:
        print(f'Processing article [{i}/{len(links)}].')
        article = Article(episode_id=episode_id, url=link)
        print(f'Scraping...')
        article = scrape_article(article)
        article.status = 'text extracted'
        print('Article scraped.')
        article.save()
        print('Changes saved.')
        i += 1
    return episode._id

# Works
def save_texts(texts: List[str], episode_name: str, episode_num: int) -> ObjectId:
    print('Creating/accessing episode...')
    episode = Episode(episode_name=episode_name, episode_num=episode_num)
    episode.save()
    print('Episode created and saved.')
    episode_id = episode._id
    print(f'Going through {len(texts)} texts.')
    for i, text in enumerate(texts, start=1):
        print(f'Processing article [{i}/{len(texts)}].')
        txt = Text(episode_id=episode_id, full_text=text)
        txt.save()
        print('Changes saved.')
    return episode._id

def create_script(episode_id: ObjectId, source_col: str):
    cursor = db[source_col].find({"episode_id": episode_id, "status": "not processed"})
    full_texts = ' '.join(text.get("full_text") for text in cursor)

    if not full_texts.strip():
        raise ValueError("No text found for this episode")

    script = generate_script(full_texts, model, tokenizer)
    return script

# Needs debugging
# def chunk_articles(episode_id: ObjectId):
#     articles_col = db['articles']
#     articles_cursor = articles_col.find({"episode_id": episode_id, "status": "text extracted"})
#     print(f'Going through {articles_col.count_documents({"episode_id": episode_id, "status": "text extracted"})} articles.')
#     for i, article in enumerate(articles_cursor, start=1):
#         print(f'Processing article {i}.')
#         article_id = article.get("_id")
#         text = article.get("full_text")
#         if not text:
#             print(f"Skipping article {article_id}: no full_text available")
#             continue
#         print(f'Chunking article...')
#         chunks = chunk_by_sentence(text)
#         print(f'Article chunked.')
#         print(f'Going through {len(chunks)} chunks.')
#         for j, chunk_text in enumerate(chunks, start=1):
#             print(f'Processing chunk {j}.')
#             print(f'Generating chunk summary...')
#             chunk_summary = generate_chunk_summary(chunk_text)
#             chunk = Chunk(article_id=article_id, chunk_text=chunk_text, chunk_summary=chunk_summary)
#             print('Chunk summary generated and chunk saved.')
#             chunk.save()
    # return article_id

# def combine_chunk_summaries(article_id: ObjectId) -> None:
#     chunks_col = db['chunks']
#     chunks_cursor = chunks_col.find({"article_id": article_id},{"status": "not recombined"})
#     combined_summary = ''
#     for chunk in chunks_cursor:
#         summary = chunk.chunk_summary
#         combined_summary += summary
#     summary = Summary(article_id=article_id, summary=combined_summary)
#     summary.save()

# def generate_episode_script(episode_id: ObjectId):
#     articles_col = db['articles']
#     articles_cursor = articles_col.find({"episode_id" : episode_id},{"status":"text etracted"})
#     source_material = ''
#     for article in articles_cursor:
#         article_id = article._id
#         summaries_col = db['summaries']
#         summaries_cursor = summaries_col.find({"article_id": article_id})
#         for summary in summaries_cursor:
#             summary += summary.summary_text

#     return generate_script(source_material)

def main():
    # gmail_service = get_gmail_service()
    # newsletter_links = get_latest_newsletter_links(gmail_service, 'dan@tldrnewsletter.com')
    # return newsletter_links
    return fetch_text()
    # chunk_articles(ObjectId('69478276dc35f7bae803b370'))

    # emails = get_lastest_emails_text(gmail_service, 'uber@uber.com')
    # return emails
    # text = extract_text(newsletter_html)
    # summary = summarize_newsletter(text)
    # audio_path = generate_audio(summary)
    # rss_url = update_feed(summary, audio_path)
    # send_episode_email(summary, rss_url, audio_path)

if __name__ == "__main__":
    # text_doc = db["texts"].find_one()
    cursor = db["texts"].find({"episode_id": ObjectId("6959d00f98e8dc6cffe0f67b"), "status": "not processed"})
    full_texts = ' '.join(text.get("full_text") for text in cursor)

    if full_texts:
        episode_id = str(ObjectId("6959d00f98e8dc6cffe0f67b"))

        response = requests.post(
            "http://localhost:8000/generate_script",
            json= {
                "source_text": full_texts,
                "episode_id": episode_id
            }
        )
        # print(response.json()["script"])
        print("Status Code:", response.status_code)
        print("Response:", response.json())
    else:
        print(create_script(ObjectId("6959d00f98e8dc6cffe0f67b"), "texts"))
