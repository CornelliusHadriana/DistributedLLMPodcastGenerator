import base64
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import unquote, urlparse
from auth.gmail_auth import get_gmail_service
import re
import uuid
from db import db

CLIENT_FILE = 'credentials.json'
GMAIL_BASE_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'

UNALLOWED_DOMAINS = [
    "tldr.tech",
    "a.tldrnewsletter.com",
    "tracking.tldrnewsletter.com",
    "advertise.tldr.tech",
    "links.tldrnewsletter.com",
    "www.linkedin.com",
    "refer.tldr.tech",
    "jobs.ashbyhq.com",
    "referralhub.page"
]
REMOVE_TEXT = "\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c\xa0\u200c Sign Up |Advertise|View Online TLDR"

def fetch_links() -> List[str]:
    gmail_service = get_gmail_service()
    newsletter_links = get_latest_newsletter_links(gmail_service, 'dan@tldrnewsletter.com')
    return newsletter_links

def create_job(source_text, sender, subject, prompt_type="acquired"):
    job = {
        "job_id": str(uuid.uuid4()),
        "source": {
            "type": "gmail",
            "sender": sender,
            "subject": subject
        },
        "input": {
            "source_text": source_text,
            "prompt_type": prompt_type,
            "model": "meta-llama/Llama-3.1-8B-Instruct"
        },
        "status": "queued",
        "output": {
            "script": None,
            "tokens_generated": None
        },
        "metrics": {
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "latency_sec": None
        },
        "error": None
    }
    db.jobs.insert_one(job)
    return job["job_id"]


def get_latest_newsletter_text(gmail_service, email):
    '''
    Returns a list of all the links from latest newsletter emails
    '''
    start_time = (datetime.now()-timedelta(days=1)).strftime('%Y/%m/%d')
    print('Fetching messages...')
    messages = _fetch_messages(gmail_service, email, start_time=start_time)
    print(f'Messages fetched. Found {len(messages)} messages.')
    texts = []
    for i, message in enumerate(messages):
        try:
            print(f'Processing message {i+1}/{len(messages)}...')
            message_id = message.get('id')
            # Get the full message object with payload
            full_message = gmail_service.users().messages().get(userId='me', id=message_id).execute()
            payload = full_message.get('payload')
            print(f'  Payload acquired for message {i+1}.')
            if payload:
                print(f'  Extracting HTML body from message {i+1}...')
                html_body = _extract_html_body(payload)
                print(f'  HTML body acquired for message {i+1}.')
                if html_body:
                    print(f'  Extracting text from message {i+1}...')
                    text = _extract_text_body(html_body)
                    print(f'  Found text in message {i+1}.')
                    text = text.replace(REMOVE_TEXT, '')
                    text = re.split(r'Love TLDR\?', text)[0]
                    if text:
                        texts.append(text)
                else:
                    print(f'  No HTML body found in message {i+1}.')
            else:
                print(f'  No payload in message {i+1}.')
        except Exception as e:
            print(f'  Error processing message {i+1}: {type(e).__name__}: {e}')

    print(f'Total links extracted: {len(texts)}')
    return texts

def get_latest_newsletter_links(gmail_service, email):
    '''
    Returns a list of all the links from latest newsletter emails
    '''
    start_time = (datetime.now()-timedelta(days=50)).strftime('%Y/%m/%d')
    print('Fetching messages...')
    messages = _fetch_messages(gmail_service, email, start_time=start_time)
    print(f'Messages fetched. Found {len(messages)} messages.')
    all_links = []
    for i, message in enumerate(messages):
        try:
            print(f'Processing message {i+1}/{len(messages)}...')
            message_id = message.get('id')
            # Get the full message object with payload
            full_message = gmail_service.users().messages().get(userId='me', id=message_id).execute()
            payload = full_message.get('payload')
            print(f'  Payload acquired for message {i+1}.')
            if payload:
                print(f'  Extracting HTML body from message {i+1}...')
                html_body = _extract_html_body(payload)
                print(f'  HTML body acquired for message {i+1}.')
                if html_body:
                    print(f'  Extracting links from message {i+1}...')
                    links = _extract_link_from_html(html_body)
                    print(f'  Found {len(links)} links in message {i+1}.')
                    if links:
                        all_links.extend(links)
                else:
                    print(f'  No HTML body found in message {i+1}.')
            else:
                print(f'  No payload in message {i+1}.')
        except Exception as e:
            print(f'  Error processing message {i+1}: {type(e).__name__}: {e}')

    print(f'Total links extracted: {len(all_links)}')
    return all_links
        

# def init_gmail_service(client_file, api_name='gmail', api_version='v1', scopes=['https://mail.google.com/readonly']):
#     return create_service(client_file, api_name, api_version, scopes)

def _fetch_messages(gmail_service, target_email: str, start_time: str) -> List[Dict]:
    '''
    Fetches a list of all message objects from after a start_time.
    '''
    all_messages = []
    user_id = 'me'
    query = f'from:{target_email} after:{start_time}'
    request = gmail_service.users().messages().list(userId=user_id, q=query)
    while request is not None:
        response = request.execute()
        messages = response.get('messages', [])
        all_messages.extend(messages)
        request = gmail_service.users().messages().list_next(request, response)

    return all_messages

def _extract_text_body(payload) -> str:
    '''
    Extract the plain text body from an email message payload.
    
    This is a private helper function that recursively searches through the
    email payload structure to find and decode the plain text body content.
    It handles various MIME structures including multipart messages.
    '''
    try:
        # If it's already a string (HTML), extract text from it
        if isinstance(payload, str):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(payload, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text

        if 'parts' in payload:
            for part in payload['parts']:
                result = _extract_text_body(part)
                if result:
                    return result
        elif payload.get('mimeType') == 'text/plain' and 'data' in payload.get('body', {}):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    except Exception as e:
        print(f'Error extracting text body: {type(e).__name__}: {e}')
    return None

def _extract_html_body(payload) -> str:
    '''
    Extract the html body from an email message payload.
    
    This is a private helper function that recursively searches through the
    email payload structure to find and decode the html body content.
    It handles various MIME structures including multipart messages.
    '''
    try:
        if 'parts' in payload:
            for part in payload['parts']:
                result = _extract_html_body(part)
                if result:
                    return result
        elif payload.get('mimeType') == 'text/html' and 'data' in payload.get('body', {}):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')  
    except Exception as e:
        print(f'Error extracting HTML body: {type(e).__name__}: {e}')
    return None

def _extract_link_from_html(html_body: str) -> List[str]:
    '''
    Docstring for _extract_link: Takes in a message body and extracts links
    '''
    soup = BeautifulSoup(html_body, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    decoded_links = []
    for tracking_link in links:
        # ensure this is an http(s) URL
        if not tracking_link.startswith(('http://', 'https://')):
            continue
        # Only decode links that have the /CL0/ pattern
        if '/CL0/' in tracking_link:
            try:
                # split only once to avoid unexpected extra slashes
                encoded_url = tracking_link.split("/CL0/", 1)[1]
                real_url = unquote(encoded_url)

                domain = urlparse(real_url).netloc
                if domain in UNALLOWED_DOMAINS:
                    continue

                decoded_links.append(real_url)
            except Exception as e:
                print(f'Error decoding tracking link: {e}')
                decoded_links.append(tracking_link)  # Keep original if decoding fails
        else:
            # Keep non-tracking links as-is
            decoded_links.append(tracking_link)
    return decoded_links


        