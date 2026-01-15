import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GCP_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not GEMINI_API_KEY or not GCP_CREDENTIALS:
    raise RuntimeError('Missing environment variables')