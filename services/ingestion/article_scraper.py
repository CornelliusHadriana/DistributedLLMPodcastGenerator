import trafilatura
from typing import List, Tuple
from playwright.sync_api import sync_playwright
from utils.files import write_text_to_file
from pathlib import Path
from services.ingestion.fetch_emails import get_latest_newsletter_links
from auth.gmail_auth import get_gmail_service
from db.database import Article

def scrape_article(article: Article) -> Article:
        try:
            print('Scraping article...')
            title, full_text = extract_text_with_playwright(article.url)
            article.title = title
            article.full_text = full_text
            print('Article scraped.')
            return article
        except Exception as e:
            raise Exception(f'Could not scrape article: {e}')
        
def extract_text_with_playwright(url: str) -> Tuple[str, str]:
    '''
    Given a url to an article, returns a tuple contain the title and text body.
    '''
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            print('Going into page...')
            page.goto(url)
            print('Successfully entered page.')

            html = page.content()
            browser.close()

            print('Extracting title...')
            title = None
            metadata = trafilatura.extract_metadata(html)
            if metadata:
                title = metadata.title
            print('Title extracted.')
            
            print('Extracing text...')
            text = trafilatura.extract(
                html,
                include_tables=True,
                include_comments=False
            )
            print('Text extracted.')

            # Use extracted values, or fallback to defaults if None
            title = title or 'Untitled'
            text = text or ''
            return title, text
    except Exception as e:
        print(f'Error scraping text {url}: {e}')
        return 'Untitled', ''
    
def save_articles_to_file(urls: List[str]) -> None:
    '''
    Given a list of urls to articles, saves each article to a separate file.
    '''
    try:
        for url in urls:
            title, text = extract_text_with_playwright(url)
            file_name = f'{title}.txt'

            cwd = Path(__file__).resolve()
            curr_dir = cwd.parent
            project_root = curr_dir.parent
            target_folder_path = project_root / 'data' / 'articles'

            if not target_folder_path.exists():
                target_folder_path.mkdir(parents=True, exist_ok=True)

            file_path = target_folder_path / file_name
     
            write_text_to_file(text, file_path)
    except Exception as e:
        print(f'Could not scrape and save urls to file {e}')
        return None
    
def save_combined_articles(urls: List[str], episode_num: int) -> None:
    '''
    Given a list of urls to articles, saves each article to a combined episode file.
    '''
    try:
        text = ''
        for url in urls:
            text += extract_text_with_playwright(url)[1]

            cwd = Path(__file__).resolve()
            curr_dir = cwd.parent
            project_root = curr_dir.parent
            target_folder_path = project_root / 'data' / 'episodes' / f'episode_{episode_num}'

            if not target_folder_path.exists():
                target_folder_path.mkdir(parents=True, exist_ok=True)

            file_path = target_folder_path / f'episode_{episode_num}_material.txt'

            write_text_to_file(text, file_path)
    except Exception as e:
        print(f'Could not scrape and savel urls to file {e}')
        return None
    
if __name__=='__main__':
    gmail_service = get_gmail_service()
    newsletter_links = get_latest_newsletter_links(gmail_service, 'dan@tldrnewsletter.com')[:5]
    # test_urls = [
    #              'https://react.dev/blog/2025/12/11/denial-of-service-and-source-code-exposure-in-react-server-components?utm_source=tldrdev',
    #              'https://www.shopify.com/news/winter-26-edition-dev?utm_source=comms_paid&utm_medium=newsletter&utm_campaign=winter26edition-launch_Q425BACADO&utm_content=tldrdev-v1',
    #              'https://openai.com/index/introducing-gpt-5-2/?utm_source=tldrdev'
    #              ]
    # text = asyncio.run(extract_text(test_urls))
    # for extracted_text in text:
    #     print(extracted_text)
    # for url in test_urls:
    #     title, text = extract_text_with_playwright(url)
    #     print(title)
    save_combined_articles(newsletter_links, 1)
    print('Success!')