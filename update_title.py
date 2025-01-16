import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
VIDEO_ID = os.getenv('MY_VIDEO_ID')

def get_authenticated_service():
    """Set up YouTube API authentication."""
    creds = None
    
    # Load credentials from oauth2.json
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    # If credentials are invalid or expired, raise error
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        else:
            print("Invalid credentials. Please ensure oauth2.json is properly configured.")
            return None

    try:
        # Build the service
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building service: {e}")
        return None

def main():
    # Validate environment variables
    required_vars = ['MY_VIDEO_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return

    print("Starting YouTube API authentication...")
    youtube = get_authenticated_service()
    
    if not youtube:
        print("Failed to authenticate with YouTube API")
        return

    print("Authenticated successfully.")
    
    try:
        # Fetch the latest comment
        print("Fetching the latest comment...")
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=VIDEO_ID,
            order="time",
            maxResults=1
        )
        comment_response = comment_request.execute()
        
        if not comment_response.get("items"):
            print("No comments found on the video.")
            return
            
        # Get commenter name
        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")
        
        # Get subscriber count
        channel_request = youtube.channels().list(
            part="statistics",
            mine=True
        )
        channel_response = channel_request.execute()
        
        if not channel_response.get("items"):
            print("Could not retrieve channel info.")
            return
            
        subscriber_count = channel_response["items"][0]["statistics"].get("subscriberCount", "0")
        
        # Create new title
        new_title = f"{commenter_display_name} is my Favourite Person they helped me gain {subscriber_count} subs"
        
        # Get current video details
        video_request = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        )
        video_response = video_request.execute()
        
        if not video_response.get("items"):
            print("Video not found or insufficient permissions.")
            return
            
        # Preserve existing snippet data
        current_snippet = video_response["items"][0]["snippet"]
        current_snippet["title"] = new_title
        
        # Update the video
        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": VIDEO_ID,
                "snippet": current_snippet
            }
        )
        update_response = update_request.execute()
        print(f"Success! Updated video title to: {new_title}")
        
    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
