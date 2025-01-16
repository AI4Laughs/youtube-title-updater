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
VIDEO_ID = os.environ.get('MY_VIDEO_ID')
SHORT_ID = os.environ.get('MY_SHORT_ID')

def log_message(message):
    """Print log message with timestamp"""
    print(f"[LOG] {message}")
    sys.stdout.flush()

def get_authenticated_service():
    """Set up YouTube API authentication"""
    log_message("Starting authentication process")
    
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            log_message("Successfully loaded oauth2.json")
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                log_message("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                log_message("Invalid credentials")
                return None
                
        return build('youtube', 'v3', credentials=creds)
        
    except Exception as e:
        log_message(f"Authentication error: {str(e)}")
        return None

def update_video_title(youtube, video_id, is_short=False):
    """Update video title"""
    try:
        log_message(f"Updating {'Short' if is_short else 'Video'}: {video_id}")
        
        # Get latest comment
        comments = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="time",
            maxResults=1
        ).execute()
        
        if not comments.get('items'):
            log_message("No comments found")
            return False
            
        commenter = comments['items'][0]['snippet']['topLevelComment']['snippet']['authorDisplayName']
        log_message(f"Latest commenter: {commenter}")
        
        if is_short:
            # Get video stats
            stats = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()
            
            if not stats.get('items'):
                log_message("Could not get video stats")
                return False
                
            views = stats['items'][0]['statistics']['viewCount']
            new_title = f"This video has {views} views thanks to {commenter} #shorts"
        else:
            # Get subscriber count
            channel = youtube.channels().list(
                part="statistics",
                mine=True
            ).execute()
            
            if not channel.get('items'):
                log_message("Could not get channel stats")
                return False
                
            subs = channel['items'][0]['statistics']['subscriberCount']
            new_title = f"{commenter} is my Favourite Person they helped me gain {subs} subs"
        
        log_message(f"Setting new title: {new_title}")
        
        # Update the title
        youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": new_title,
                    "categoryId": "22"  # Default to People & Blogs
                }
            }
        ).execute()
        
        log_message("Title updated successfully")
        return True
        
    except HttpError as e:
        log_message(f"YouTube API error: {str(e)}")
        return False
    except Exception as e:
        log_message(f"Error updating title: {str(e)}")
        return False

def main():
    log_message("=== Starting YouTube Title Update Script ===")
    
    # Check environment variables
    if not VIDEO_ID and not SHORT_ID:
        log_message("Error: No video IDs found in environment variables")
        return
        
    youtube = get_authenticated_service()
    if not youtube:
        log_message("Failed to create YouTube service")
        return
        
    if VIDEO_ID:
        success = update_video_title(youtube, VIDEO_ID, is_short=False)
        log_message(f"Regular video update: {'Success' if success else 'Failed'}")
        
    if SHORT_ID:
        success = update_video_title(youtube, SHORT_ID, is_short=True)
        log_message(f"Short video update: {'Success' if success else 'Failed'}")
        
    log_message("=== Script Completed ===")

if __name__ == "__main__":
    main()
