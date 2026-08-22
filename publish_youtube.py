"""
YouTube Upload & Thumbnail Publishing Module (Raaga Blumes)
Uses OAuth refresh token to upload 1-hour HD meditation videos and set custom thumbnails.
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def get_authenticated_service():
    """Authenticate using refresh token from environment variables."""
    client_id = (os.getenv('YOUTUBE_CLIENT_ID') or os.getenv('YT_CLIENT_ID', '')).strip()
    client_secret = (os.getenv('YOUTUBE_CLIENT_SECRET') or os.getenv('YT_CLIENT_SECRET', '')).strip()
    refresh_token = (os.getenv('YOUTUBE_REFRESH_TOKEN') or os.getenv('YT_REFRESH_TOKEN', '')).strip()

    def mask(s):
        return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "MISSING"

    print(f"[youtube] Client ID: {mask(client_id)}")
    print(f"[youtube] Client Secret: {mask(client_secret)}")
    print(f"[youtube] Refresh Token: {mask(refresh_token)}")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing YouTube credentials! Set YT_CLIENT_ID, YT_CLIENT_SECRET, and YT_REFRESH_TOKEN in environment."
        )

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )

    try:
        creds.refresh(Request())
    except Exception as e:
        if "invalid_grant" in str(e).lower():
            print("\n❌ [youtube] AUTH ERROR: Refresh token has EXPIRED or been REVOKED.")
        raise

    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(video_path, title, description, tags=None, category_id='10', privacy_status='public'):
    """
    Uploads a video to YouTube.
    Category 10 = Music
    """
    if tags is None:
        tags = ['Bansuri', 'RaagBageshri', 'IndianClassical', 'MeditationMusic', 'DeepSleep', 'RelaxingMusic', 'RaagaBlumes', '432Hz']

    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=10 * 1024 * 1024,
        resumable=True,
        mimetype='video/mp4'
    )

    print(f"[youtube] Uploading Video: {title}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  --> Upload progress: {pct}%")

    video_id = response.get('id')
    print(f"[youtube] Upload Complete! Video ID: {video_id}")
    print(f"[youtube] URL: https://youtu.be/{video_id}")
    return video_id

def set_video_thumbnail(video_id, thumbnail_path):
    """Sets custom thumbnail on uploaded YouTube video."""
    if not os.path.exists(thumbnail_path):
        print(f"[youtube] Thumbnail path not found: {thumbnail_path}")
        return False

    youtube = get_authenticated_service()
    print(f"[youtube] Setting custom thumbnail for Video ID: {video_id}...")
    try:
        media = MediaFileUpload(str(thumbnail_path), mimetype='image/jpeg')
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        print("[youtube] Thumbnail successfully set!")
        return True
    except Exception as e:
        print(f"[youtube] Failed to set thumbnail: {e}")
        return False
