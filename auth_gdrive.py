"""
Authenticate with Google Drive for downloading CMIP6 data.

Run this once to generate a fresh token. It will open your browser
for OAuth consent, then save the token for future use.

Usage:
    python auth_gdrive.py
"""
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

CREDS_FILE = Path('/home/kai/.claude/skills/update-radio-archive/credentials.json')
TOKEN_FILE = Path('/home/kai/Documents/Opus46Dixon_FirstShot/data/cmip6/gdrive_token.json')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def authenticate():
    creds = None

    # Try existing token first
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or re-authenticate
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("Token refreshed successfully.")
        except Exception:
            creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        print("Authentication successful!")

    # Save token
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, 'w') as f:
        f.write(creds.to_json())
    print(f"Token saved to {TOKEN_FILE}")

    # Quick test
    from googleapiclient.discovery import build
    service = build('drive', 'v3', credentials=creds)
    about = service.about().get(fields='user').execute()
    print(f"Authenticated as: {about['user']['emailAddress']}")

    return creds


if __name__ == '__main__':
    authenticate()
