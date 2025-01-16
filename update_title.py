import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

print("=== Starting YouTube API Read Test ===")

try:
    # Load credentials
    print("\n1. Loading credentials...")
    with open('oauth2.json', 'r') as f:
        creds_data = json.load(f)
        print("✓ Credentials loaded")
        print(f"Available credential keys: {list(creds_data.keys())}")

    # Create credentials object
    print("\n2. Creating credentials object...")
    creds = Credentials.from_authorized_user_info(
        creds_data,
        ['https://www.googleapis.com/auth/youtube.force-ssl']
    )
    print("✓ Credentials object created")

    # Build service
    print("\n3. Building YouTube service...")
    youtube = build('youtube', 'v3', credentials=creds)
    print("✓ YouTube service built")

    # Get video ID from environment
    video_id = os.environ.get('MY_VIDEO_ID')
    print(f"\n4. Checking video ID: {video_id if video_id else 'Not found'}")

    if not video_id:
        raise ValueError("No video ID found in environment variables")

    # Try to read video details
    print("\n5. Attempting to read video details...")
    video_response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()
    
    if 'items' in video_response:
        print("✓ Successfully read video details")
        print(f"Current title: {video_response['items'][0]['snippet']['title']}")
    else:
        print("✗ No video found with this ID")

    # Try to read comments
    print("\n6. Attempting to read video comments...")
    comments_response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=1
    ).execute()
    
    if 'items' in comments_response:
        comment = comments_response['items'][0]['snippet']['topLevelComment']['snippet']
        print("✓ Successfully read comment")
        print(f"Latest comment by: {comment['authorDisplayName']}")
        print(f"Comment text: {comment['textDisplay']}")
    else:
        print("✗ No comments found")

except Exception as e:
    print(f"\n❌ ERROR OCCURRED:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    raise

print("\n=== Test Complete ===")
