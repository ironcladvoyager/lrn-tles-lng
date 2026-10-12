"""
YouTube Publisher for Learn English with Tales
Uploads 16:9 Full HD story podcast videos to YouTube with custom thumbnail, metadata, and tags.
"""
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

def get_authenticated_service():
    """Authenticate using refresh token from environment variables or local token file."""
    client_id = (os.getenv('YT_CLIENT_ID') or os.getenv('YOUTUBE_CLIENT_ID', '')).strip().strip('"').strip("'")
    client_secret = (os.getenv('YT_CLIENT_SECRET') or os.getenv('YOUTUBE_CLIENT_SECRET', '')).strip().strip('"').strip("'")
    refresh_token = (os.getenv('YT_REFRESH_TOKEN') or os.getenv('YOUTUBE_REFRESH_TOKEN', '')).strip().strip('"').strip("'")

    if not all([client_id, client_secret, refresh_token]):
        # Try local token file fallback
        candidate_json = Path(r"C:\Users\kreg9\Downloads\kreggscode\open code\bots\youtube refresh tokens bot\token_Learn English with tales.json")
        if candidate_json.exists():
            try:
                with open(candidate_json, encoding="utf-8") as f:
                    data = json.load(f)
                    client_id = client_id or data.get("client_id", "")
                    client_secret = client_secret or data.get("client_secret", "")
                    refresh_token = refresh_token or data.get("refresh_token", "")
            except Exception:
                pass

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing YouTube credentials! Ensure YT_CLIENT_ID, YT_CLIENT_SECRET, and YT_REFRESH_TOKEN are set in .env"
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
        print(f"[youtube] ⚠️ Auth refresh error: {e}")
        raise

    return build('youtube', 'v3', credentials=creds)

def upload_video_to_youtube(video_path, metadata, privacy_status="public", category_id="27"):
    """
    Uploads the video to YouTube. Category 27 = Education.
    """
    youtube = get_authenticated_service()

    title = metadata.get("title", "Learn English with Tales")[:100]
    description = metadata.get("description", "New episode of Learn English with Tales!")
    tags = metadata.get("tags", ["Learn English", "Story Podcast", "English Tales"])

    clean_tags = []
    tot_len = 0
    for t in tags:
        t_clean = str(t)[:30]
        if tot_len + len(t_clean) + 1 < 450:
            clean_tags.append(t_clean)
            tot_len += len(t_clean) + 1

    body = {
        'snippet': {
            'title': title,
            'description': description[:4900],
            'tags': clean_tags,
            'categoryId': category_id,
            'defaultLanguage': 'en',
            'defaultAudioLanguage': 'en'
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': True
        }
    }

    media = MediaFileUpload(
        str(video_path),
        chunksize=2 * 1024 * 1024,
        resumable=True,
        mimetype='video/mp4'
    )

    print(f"[youtube] 🚀 Uploading video: {title}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retries = 0
    max_retries = 5

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"[youtube] ⏳ Progress: {pct}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                retries += 1
                if retries > max_retries:
                    raise
                wait = 2 ** retries
                print(f"[youtube] ⚠️ Server error {e.resp.status}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            retries += 1
            if retries > max_retries:
                raise
            wait = 2 ** retries
            print(f"[youtube] ⚠️ Unexpected error: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    video_id = response.get('id')
    video_url = f"https://youtube.com/watch?v={video_id}"
    print(f"[youtube] ✅ Upload complete!")
    print(f"[youtube] 📺 Video URL: {video_url}")

    # Upload custom thumbnail
    thumbnail_path = metadata.get("thumbnail_path")
    if not thumbnail_path or not Path(thumbnail_path).exists():
        candidate_thumb = Path(video_path).parent / "thumbnail.jpg"
        if candidate_thumb.exists():
            thumbnail_path = str(candidate_thumb)

    if thumbnail_path and Path(thumbnail_path).exists():
        print(f"[youtube] 🖼️ Uploading custom thumbnail: {thumbnail_path}")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype='image/jpeg')
            ).execute()
            print(f"[youtube] ✅ Custom thumbnail successfully uploaded!")
        except Exception as e:
            print(f"[youtube] ⚠️ Thumbnail upload note: {e}")

    return {
        "id": video_id,
        "url": video_url,
        "response": response
    }

if __name__ == "__main__":
    if len(sys.argv) > 2:
        v_p = sys.argv[1]
        m_p = sys.argv[2]
        with open(m_p, "r", encoding="utf-8") as f:
            meta = json.load(f)
        upload_video_to_youtube(v_p, meta)
    else:
        print("Usage: python publish_youtube.py <video_path> <metadata_json_path>")
