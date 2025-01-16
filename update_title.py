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
SHORT_ID = os.getenv('MY_SHORT_ID')

def get_authenticated_service():
    """Set up YouTube API authentication."""
    creds = None
    
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

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
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building service: {e}")
        return None

def get_video_stats(youtube, video_id):
    """Fetch video statistics including view count."""
    try:
        stats_request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        stats_response = stats_request.execute()
        
        if not stats_response.get("items"):
            return None
            
        return stats_response["items"][0]["statistics"]
    except Exception as e:
        print(f"Error fetching video statistics: {e}")
        return None

def format_view_count(view_count):
    """Format view count to be more readable."""
    count = int(view_count)
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    return str(count)

def update_video_title(youtube, video_id, is_short=False):
    """Update title for either a regular video or a Short."""
    try:
        # Fetch the latest comment for this video
        print(f"Fetching latest comment for {'Short' if is_short else 'Video'} {video_id}...")
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="time",
            maxResults=1
        )
        comment_response = comment_request.execute()
        
        if not comment_response.get("items"):
            print(f"No comments found on the {'Short' if is_short else 'Video'}.")
            return False
            
        # Get commenter name
        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")
        
        if is_short:
            # Get video statistics for Short
            video_stats = get_video_stats(youtube, video_id)
            if not video_stats:
                print("Could not retrieve video statistics.")
                return False
                
            view_count = format_view_count(video_stats.get("viewCount", "0"))
            new_title = f"This Short has {view_count} views thanks to {commenter_display_name} #shorts"
        else:
            # Get subscriber count for regular video
            channel_request = youtube.channels().list(
                part="statistics",
                mine=True
            )
            channel_response = channel_request.execute()
            
            if not channel_response.get("items"):
                print("Could not retrieve channel info.")
                return False
                
            subscriber_count = channel_response["items"][0]["statistics"].get("subscriberCount", "0")
            new_title = f"{commenter_display_name} is my Favourite Person they helped me gain {subscriber_count} subs"
        
        # Get current video details
        video_request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        video_response = video_request.execute()
        
        if not video_response.get("items"):
            print(f"{'Short' if is_short else 'Video'} not found or insufficient permissions.")
            return False
            
        # Preserve existing snippet data
        current_snippet = video_response["items"][0]["snippet"]
        current_snippet["title"] = new_title
        
        # Update the video
        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": current_snippet
            }
        )
        update_response = update_request.execute()
        print(f"Success! Updated {'Short' if is_short else 'Video'} title to: {new_title}")
        return True
        
    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__}: {str(e)}")
        return False

def main():
    # Validate environment variables
    required_vars = ['MY_VIDEO_ID', 'MY_SHORT_ID']
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
    
    # Update regular video
    if VIDEO_ID:
        success = update_video_title(youtube, VIDEO_ID, is_short=False)
        print(f"Regular video update {'successful' if success else 'failed'}")
    
    # Update Short
    if SHORT_ID:
        success = update_video_title(youtube, SHORT_ID, is_short=True)
        print(f"Short update {'successful' if success else 'failed'}")

if __name__ == "__main__":
    main()
