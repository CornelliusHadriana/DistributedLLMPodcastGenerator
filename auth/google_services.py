from __future__ import annotations
import os

from googleapiclient.discovery import build as gapi_build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

def create_service(client_secret_file, api_name, api_version, scopes=None, prefix=''):
     CLIENT_SECRET_FILE = client_secret_file
     API_SERVICE_NAME = api_name
     API_VERSION = api_version
     SCOPES = scopes

     creds = None
     # Get absolute path where file is located
     working_dir = os.path.dirname(os.path.abspath(__file__))

     token_dir = 'token files'
     token_file = f'token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json'

     ### Check if token dir exists first, if not, create the folder
     if not os.path.exists(os.path.join(working_dir, token_dir)):
          os.mkdir(os.path.join(working_dir, token_dir))

     if os.path.exists(os.path.join(working_dir, token_dir, token_file)):
          creds = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)

     if not creds or not creds.valid:
          if creds and creds.expired and creds.refresh_token:
               creds.refresh(Request())
          else:
               flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
               creds = flow.run_local_server(port=0)
            
          with open(os.path.join(working_dir, token_dir, token_file), 'w') as token:
               token.write(creds.to_json())

     try:
          service = gapi_build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
          print(API_SERVICE_NAME, API_VERSION, 'service created successfully')
          return service
     except Exception as e:
          print(e)
          print(f'Failed to create service instance for {API_SERVICE_NAME}')
          os.remove(os.path.join(working_dir, token_dir, token_file))
          return None

                    
