import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser

# Read secrets from environment variables
CLIENT_ID = os.getenv("MY_CLIENT_ID")
CLIENT_SECRET = os.getenv("MY_CLIENT_SECRET")
VIDEO_ID = os.getenv("MY_VIDEO_ID")

# Debugging: Print environment variables
print(f"CLIENT_ID: {CLIENT_ID}")
print(f"VIDEO_ID: {VIDEO_ID}")

# YouTube Data API scope
OAUTH_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"  # Local/desktop OAuth flow

def get_authenticated_service():
    """
    Authenticates the user via OAuth2:
      - Checks if we have valid credentials in oauth2.json
      - If invalid, prompts user to log in & authorize via a browser
    """
    flow = OAuth2WebServerFlow(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scope=OAUTH_SCOPE,
        redirect_uri=REDIRECT_URI
    )
    storage = Storage("oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, argparser.parse_args([]))

    return build("youtube", "v3", credentials=credentials)

def main():
    youtube = get_authenticated_service()

    try:
        # 1. Fetch the latest top-level comment from your video
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=VIDEO_ID,
            order="time",   # newest first
            maxResults=1
        )
        comment_response = comment_request.execute()

        if not comment_response.get("items"):
            print("No comments found on the video.")
            return

        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")

        # 2. Get your own channel’s subscriber count
        channel_request = youtube.channels().list(
            part="statistics",
            mine=True
        )
        channel_response = channel_request.execute()

        if not channel_response.get("items"):
            print("Could not retrieve your channel info.")
            return

        subscriber_count = channel_response["items"][0]["statistics"].get("subscriberCount", "0")

        # 3. Construct the new title string
        new_title = f"{commenter_display_name} is my Favourite Person they helped me gain {subscriber_count} subs"

        # 4. Fetch the existing video snippet to keep categoryId intact
        video_request = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        )
        video_response = video_request.execute()

        if not video_response.get("items"):
            print("Video not found or insufficient permissions.")
            return

        category_id = video_response["items"][0]["snippet"].get("categoryId", "22")  # fallback to "22" = People & Blogs

        # 5. Update the video title
        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": VIDEO_ID,
                "snippet": {
                    "title": new_title,
                    "categoryId": category_id
                }
            }
        )
