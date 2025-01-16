import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

def test_connection():
    print("Starting YouTube API connection test...")
    
    try:
        # Load credentials
        print("Loading credentials...")
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
        
        # Print credential structure (without sensitive data)
        print("Credential keys present:", list(creds_data.keys()))
        
        # Create credentials object
        creds = Credentials.from_authorized_user_info(creds_data, ['https://www.googleapis.com/auth/youtube.force-ssl'])
        
        # Build service
        print("Building YouTube service...")
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Test API connection
        print("Testing API connection...")
        request = youtube.channels().list(
            part="snippet",
            mine=True
        )
        response = request.execute()
        
        if 'items' in response:
            print("Successfully connected to YouTube API!")
            print(f"Found {len(response['items'])} channel(s)")
            return True
        else:
            print("Connection successful but no channel found")
            return False
            
    except Exception as e:
        print(f"Error during test: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
