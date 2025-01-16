import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import sys

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
VIDEO_ID = os.getenv('MY_VIDEO_ID')
SHORT_ID = os.getenv('MY_SHORT_ID')

def log_debug(message):
    """Print debug message with timestamp"""
    print(f"[DEBUG] {message}", flush=True)
    sys.stdout.flush()

def verify_credentials(creds):
    """Verify if credentials are valid and have correct permissions"""
    if not creds:
        log_debug("No credentials found")
        return False
    
    if not creds.valid:
        log_debug("Credentials are invalid")
        return False
    
    if creds.expired:
        log_debug("Credentials are expired")
        return False
        
    return True

def get_authenticated_service():
    """Set up YouTube API authentication with detailed logging"""
    creds = None
    
    log_debug("Starting authentication process")
    
    try:
        log_debug("Attempting to read oauth2.json")
        with open('oauth2.json', 'r') as f:
            file_content = f.read()
            log_debug(f"oauth2.json length: {len(file_content)} characters")
            creds_data = json.loads(file_content)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except FileNotFoundError:
        log_debug("oauth2.json file not found")
        return None
    except json.JSONDecodeError as e:
        log_debug(f"Error parsing oauth2.json: {e}")
        return None
    except Exception as e:
        log_debug(f"Error loading credentials: {type(e).__name__}: {str(e)}")
        return None

    if not verify_credentials(creds):
        try:
            if creds and creds.expired and creds.refresh_token:
                log_debug("Attempting to refresh expired credentials")
                creds.refresh(Request())
                log_debug("Credentials refreshed successfully")
            else:
                log_debug("Unable to refresh credentials - no valid refresh token")
                return None
        except Exception as e:
            log_debug(f"Error refreshing credentials: {type(e).__name__}: {str(e)}")
            return None

    try:
        log_debug("Building YouTube API service")
        service = build('youtube', 'v3', credentials=creds)
        
        # Verify API access
        log_debug("Verifying API access")
        test_request = service.channels().list(
            part="snippet",
            mine=True
        )
        test_request.execute()
        log_debug("API access verified successfully")
        
        return service
    except Exception as e:
        log_debug(f"Error building service: {type(e).__name__}: {str(e)}")
        return None

def update_video_title(youtube, video_id, is_short=False):
    """Update title with detailed logging"""
    try:
        video_type = 'Short' if is_short else 'Video'
        log_debug(f"Starting update process for {video_type} {video_id}")
        
        # Verify video exists and is accessible
        log_debug(f"Verifying {video_type} exists")
        video_request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        video_response = video_request.execute()
        
        if not video_response.get("items"):
            log_debug(f"{video_type} not found or not accessible")
            return False
        
        # Fetch comments
        log_debug(f"Fetching comments for {video_type}")
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="time",
            maxResults=1
        )
        comment_response = comment_request.execute()
        log_debug(f"Comment response received: {json.dumps(comment_response, indent=2)}")
        
        if not comment_response.get("items"):
            log_debug(f"No comments found on {video_type}")
            return False
            
        # Get commenter name
        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")
        log_debug(f"Latest commenter: {commenter_display_name}")
        
        if is_short:
            # Get video statistics
            log_debug("Fetching Short statistics")
            stats_request = youtube.videos().list(
                part="statistics",
                id=video_id
            )
            stats_response = stats_request.execute()
            log_debug(f"Statistics response: {json.dumps(stats_response, indent=2)}")
            
            if not stats_response.get("items"):
                log_debug("Could not retrieve video statistics")
                return False
                
            view_count = stats_response["items"][0]["statistics"].get("viewCount", "0")
            formatted_views = format_view_count(view_count)
            new_title = f"This video has {formatted_views} views thanks to {commenter_display_name} #shorts"
        else:
            # Get subscriber count
            log_debug("Fetching channel statistics")
            channel_request = youtube.channels().list(
                part="statistics",
                mine=True
            )
            channel_response = channel_request.execute()
            log_debug(f"Channel response: {json.dumps(channel_response, indent=2)}")
            
            if not channel_response.get("items"):
                log_debug("Could not retrieve channel info")
                return False
                
            subscriber_count = channel_response["items"][0]["statistics"].get("subscriberCount", "0")
            new_title = f"{commenter_display_name} is my Favourite Person they helped me gain {subscriber_count} subs"
        
        log_debug(f"Attempting to update title to: {new_title}")
        
        # Update the video
        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": new_title,
                    "categoryId": video_response["items"][0]["snippet"]["categoryId"]
                }
            }
        )
        update_response = update_request.execute()
        log_debug(f"Update response: {json.dumps(update_response, indent=2)}")
        log_debug(f"Successfully updated {video_type} title")
        return True
        
    except HttpError as e:
        log_debug(f"HTTP error occurred: Status {e.resp.status}")
        log_debug(f"Error details: {e.content}")
        return False
    except Exception as e:
        log_debug(f"Unexpected error: {type(e).__name__}: {str(e)}")
        return False

def format_view_count(view_count):
    """Format view count to be more readable"""
    count = int(view_count)
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    return str(count)

def main():
    log_debug("=== Starting YouTube Title Update Script ===")
    
    # Verify environment variables
    log_debug("Checking environment variables")
    for var in ['MY_VIDEO_ID', 'MY_SHORT_ID', 'OAUTH_JSON']:
        value = os.getenv(var)
        log_debug(f"{var} present: {bool(value)}")
        if value:
            log_debug(f"{var} length: {len(value)} characters")

    youtube = get_authenticated_service()
    
    if not youtube:
        log_debug("Failed to create YouTube service")
        return

    log_debug("YouTube service created successfully")
    
    # Update regular video
    if VIDEO_ID:
        success = update_video_title(youtube, VIDEO_ID, is_short=False)
        log_debug(f"Regular video update {'successful' if success else 'failed'}")
    
    # Update Short
    if SHORT_ID:
        success = update_video_title(youtube, SHORT_ID, is_short=True)
        log_debug(f"Short update {'successful' if success else 'failed'}")

    log_debug("=== Script Completed ===")

if __name__ == "__main__":
    main()
