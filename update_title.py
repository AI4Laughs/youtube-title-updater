from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run_flow, argparser

# ------------------------------------------------------------------
# 1. FILL IN YOUR OAUTH CREDENTIALS FROM THE GOOGLE CLOUD CONSOLE
# ------------------------------------------------------------------
CLIENT_ID = "914043930815-0u788ic1d823jgcjooo5n54pj6fgg9rj.apps.googleusercontent.com"
CLIENT_SECRET = "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"

# The scope we need for managing YouTube videos and comments
OAUTH_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"

# For desktop or local testing, use the "oob" redirect
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

# ------------------------------------------------------------------
# 2. SPECIFY THE YOUTUBE VIDEO ID YOU WANT TO UPDATE
#    (e.g., "abcd1234EfG" part from "https://www.youtube.com/watch?v=abcd1234EfG")
# ------------------------------------------------------------------
VIDEO_ID = "VIDEO_ID_HERE"


def get_authenticated_service():
    """
    This function handles OAuth authentication.
    - It checks if we already have valid credentials in `oauth2.json`.
    - If not, it starts the browser-based flow for you to sign in and authorize.
    - After authorization, it saves your refresh tokens so you won't need to log in again.
    """
    flow = OAuth2WebServerFlow(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scope=OAUTH_SCOPE,
        redirect_uri=REDIRECT_URI
    )

    # Storage is where we keep our tokens on disk
    storage = Storage("oauth2.json")
    credentials = storage.get()

    # If we don't have credentials yet, or they're invalid, do the browser flow
    if credentials is None or credentials.invalid:
        # argparser helps parse command-line arguments for run_flow
        credentials = run_flow(flow, storage, argparser.parse_args([]))

    # Build and return a YouTube service object
    return build("youtube", "v3", credentials=credentials)


def main():
    youtube = get_authenticated_service()

    try:
        # ------------------------------------------------------------------
        # 3. Fetch the LATEST (newest) COMMENT on the specified video
        # ------------------------------------------------------------------
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=VIDEO_ID,
            order="time",   # "time" = newest first
            maxResults=1
        )
        comment_response = comment_request.execute()

        if not comment_response.get("items"):
            print("No comments found on the video.")
            return

        # Extract the snippet of the top-level comment
        top_comment_snippet = (
            comment_response["items"][0]
            ["snippet"]
            ["topLevelComment"]
            ["snippet"]
        )

        # Attempt to get the commenter's channel ID
        commenter_channel_id = top_comment_snippet.get("authorChannelId", {}).get("value", "UnknownUser")

        # ------------------------------------------------------------------
        # 4. Fetch YOUR channel's subscriber count
        # ------------------------------------------------------------------
        channel_request = youtube.channels().list(
            part="statistics",
            mine=True
        )
        channel_response = channel_request.execute()

        if not channel_response.get("items"):
            print("Could not retrieve your channel info.")
            return

        subscriber_count = channel_response["items"][0]["statistics"].get("subscriberCount", "0")

        # ------------------------------------------------------------------
        # 5. Construct the NEW VIDEO TITLE
        # ------------------------------------------------------------------
        new_title = f"{commenter_channel_id} is my Favourite Person they helped me gain {subscriber_count} subs"

        # ------------------------------------------------------------------
        # 6. Update the VIDEO TITLE on YouTube
        # ------------------------------------------------------------------
        # First, get the existing snippet so we don't lose the categoryId or other metadata
        video_request = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        )
        video_response = video_request.execute()

        if not video_response.get("items"):
            print("Video not found, or you don't have permission to edit it.")
            return

        # Keep the existing categoryId (or set a default, like "22" for People & Blogs)
        category_id = video_response["items"][0]["snippet"].get("categoryId", "22")

        # Now update with the new title
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
        update_request.execute()

        print(f"Success! Updated video title to:\n{new_title}")

    except HttpError as e:
        print(f"An HTTP error occurred: {e}")


if __name__ == "__main__":
    main()
