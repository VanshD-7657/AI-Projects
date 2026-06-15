import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# Request both Spreadsheets and Drive File access
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
CLIENT_SECRET_FILE = 'client_secret_488436259548-smo5lev7jti3pq4mujvif92cgit1nh22.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'

def get_sheets_service():
    """Initializes and returns the Google Sheets API service."""
    creds = None
    # Load credentials if token.json exists
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logger.info("Loaded credentials from token.json")
        except Exception as e:
            logger.warning(f"Failed to load token.json: {e}")

    # If credentials are not valid or do not match requested scopes, refresh or log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("Refreshed expired credentials")
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"Client secret file '{CLIENT_SECRET_FILE}' not found. "
                    "Cannot authenticate with Google Sheets."
                )
            
            logger.info("Starting local server OAuth flow to authorize Google Sheets and Drive access...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save credentials for the next run
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
                logger.info("Saved credentials to token.json")

    return build('sheets', 'v4', credentials=creds), creds

def upload_image_to_drive(creds, filepath: str) -> str:
    """
    Uploads a local image file to Google Drive and shares it publicly
    so it can be displayed in-cell using the =IMAGE() formula.
    Returns the file ID.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Local image file not found for upload: {filepath}")

    logger.info(f"Uploading image '{filepath}' to Google Drive...")
    drive_service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': f"Post_Visual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
        'mimeType': 'image/png'
    }
    media = MediaFileUpload(filepath, mimetype='image/png', resumable=True)

    # Upload the file
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    file_id = uploaded_file.get('id')
    logger.info(f"Image uploaded successfully to Google Drive. File ID: {file_id}")

    # Grant public read permission to the uploaded file (required for Google Sheets =IMAGE formula to read it)
    logger.info("Sharing Google Drive file publicly...")
    permission = {
        'role': 'reader',
        'type': 'anyone'
    }
    drive_service.permissions().create(
        fileId=file_id,
        body=permission
    ).execute()
    logger.info("Google Drive image shared successfully.")

    return file_id

def append_post_to_sheet(
    sheet_id: str,
    date_str: str,
    topic: str,
    image_path_or_url: Optional[str],
    content: str,
    post_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates, uploads images to Google Drive, and appends a row to the Google Sheet.
    Returns the JSON representation of the added row.
    """
    # 1. Validation
    if not date_str:
        # Fallback to current date in YYYY-MM-DD
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    if not topic or not topic.strip():
        raise ValueError("Post Topic is required and cannot be empty.")
        
    if not content or not content.strip():
        raise ValueError("Post Content is required and cannot be empty.")

    # Get services and credentials
    service, creds = get_sheets_service()

    # Determine image field value
    if not image_path_or_url or not image_path_or_url.strip() or image_path_or_url.lower() == "none":
        image_val = "No Image Generated"
    else:
        # If it's a URL, use =IMAGE("url")
        if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
            image_val = f'=IMAGE("{image_path_or_url}")'
        else:
            try:
                # Local file: Upload to Google Drive and embed in-cell using =IMAGE("drive_download_url")
                file_id = upload_image_to_drive(creds, image_path_or_url)
                direct_download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
                image_val = f'=IMAGE("{direct_download_url}")'
            except Exception as e:
                logger.error(f"Failed to upload image to Google Drive: {e}")
                # Fallback to file path link if upload fails
                abs_path = os.path.abspath(image_path_or_url).replace("\\", "/")
                file_url = f"file:///{abs_path}"
                image_val = f'=HYPERLINK("{file_url}", "View Local Image (Upload Failed)")'

    # Format post URL
    formatted_post_url = "Draft (Not Published)"
    if post_url:
        if post_url.startswith("http://") or post_url.startswith("https://"):
            formatted_post_url = f'=HYPERLINK("{post_url}", "View LinkedIn Post")'
        else:
            formatted_post_url = post_url

    # 2. Check and write headers if sheet is empty
    try:
        sheet_data = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range="A1:E1"
        ).execute()
        values = sheet_data.get('values', [])
    except Exception as e:
        logger.error(f"Failed to read sheet header: {e}")
        raise e

    if not values or not values[0]:
        # Sheet is empty, write the headers first (5 columns)
        headers = ["Current Date", "Post Topic", "Post Image URL", "Post Content", "LinkedIn Post URL"]
        logger.info("Sheet is empty. Writing header row...")
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="A1:E1",
            valueInputOption="USER_ENTERED",
            body={'values': [headers]}
        ).execute()

    # 3. Append the post row
    row_data = [date_str, topic, image_val, content, formatted_post_url]
    body = {
        'values': [row_data]
    }
    
    logger.info("Appending row to sheet...")
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="A1:E",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()
    
    logger.info("Successfully added row to Google Sheet!")
    
    # Return expected output structure
    return {
        "date": date_str,
        "post_topic": topic,
        "post_image": image_path_or_url if image_path_or_url else "No Image Generated",
        "post_content": content,
        "post_url": post_url if post_url else "Draft (Not Published)"
    }

if __name__ == "__main__":
    # Test/CLI usage
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    parser = argparse.ArgumentParser(description="Google Sheets Content Engine Logger")
    parser.add_argument("--sheet-id", type=str, required=True, help="Google Sheet ID")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (defaults to current date)")
    parser.add_argument("--topic", type=str, required=True, help="Post Topic")
    parser.add_argument("--image", type=str, help="Post Image URL or path")
    parser.add_argument("--content", type=str, required=True, help="Post Content")
    
    args = parser.parse_args()
    
    try:
        # Get sheet service to trigger OAuth re-auth if needed
        _, creds = get_sheets_service()
        
        result = append_post_to_sheet(
            sheet_id=args.sheet_id,
            date_str=args.date,
            topic=args.topic,
            image_path_or_url=args.image,
            content=args.content
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
