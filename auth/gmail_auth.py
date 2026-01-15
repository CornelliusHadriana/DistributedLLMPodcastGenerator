from __future__ import annotations
from .google_services import create_service
import os

CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'gmail_oauth.json')
CLIENT_SECRET_FILE = os.path.abspath(CLIENT_SECRET_FILE)

API_NAME = 'gmail'
API_VERSION = 'v1'

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]

def get_gmail_service():
    """
    Initialize and authenticate the Gmail API service.
    
    This function creates an authenticated Gmail service object that can be used
    to interact with the Gmail API. It handles OAuth 2.0 authentication using
    the provided credentials file.
    
    Args:
        client_file (str): Path to the Google OAuth 2.0 credentials JSON file.
            This file should be downloaded from the Google Cloud Console and
            contains your client ID and client secret.
        api_name (str, optional): Name of the Google API to use. 
            Defaults to 'gmail'.
        api_version (str, optional): Version of the Gmail API to use. 
            Defaults to 'v1'.
        scopes (list, optional): List of OAuth 2.0 scopes defining the level of
            access required. Defaults to ['https://mail.google.com/readonly']
            which provides read-only access to all resources and metadata.
            For full access, use ['https://mail.google.com/'].
    
    Returns:
        Resource: An authenticated Gmail API service object that can be used
            to make API calls.
    
    Example:
        >>> service = init_gmail_service('credentials.json')
        >>> # Use service to call Gmail API methods
        >>> messages = service.users().messages().list(userId='me').execute()
    
    Note:
        On first run, this will open a browser window for OAuth authentication.
        The authentication token will be cached for subsequent uses.
    """
    service = create_service(
        client_secret_file=CLIENT_SECRET_FILE,
        api_name=API_NAME,
        api_version=API_VERSION,
        scopes=SCOPES
        )
    
    return service

if __name__=='__main__':
    get_gmail_service()