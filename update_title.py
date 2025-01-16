import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

print("=== Starting Minimal YouTube API Test ===")

try:
    # Load credentials
    print("Loading credentials...")
    with open('oauth2.json', 'r') as f:
        creds_data = json.load(f)
        print("Credentials loaded successfully")
        print(f"Available keys: {list(creds_data.keys())}")

    # Create credentials object
    print("\nCreating credentials object...")
    creds = Credentials.from_authorized_user_info(
        creds_data,
        ['https://www.googleapis.com/auth/youtube.force-ssl']
    )
    print("Credentials object created")

    # Build service
    print("\nBuilding YouTube service...")
    youtube = build('youtube', 'v3', credentials=creds)
    print("YouTube service built successfully")

    # Test simple API call
    print("\nTesting API call...")
    request = youtube.channels().list(
        part="snippet",
        mine=True
    )
    response = request.execute()
    print("API call successful!")
    print(f"Channel title: {response['items'][0]['snippet']['title']}")

except Exception as e:
    print(f"\nERROR: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    raise

print("\n=== Test Complete ===")
