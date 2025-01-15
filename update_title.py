print("Starting YouTube API authentication...")
youtube = get_authenticated_service()
print("Authenticated successfully.")

try:
    print("Fetching the latest comment...")
    comment_request = youtube.commentThreads().list(
        part="snippet",
        videoId=VIDEO_ID,
        order="time",
        maxResults=1
    )
    comment_response = comment_request.execute()
    print("Comment fetched successfully.")
    print(f"Response: {comment_response}")
    
    if not comment_response.get("items"):
        print("No comments found on the video.")
        return

    print("Extracting comment details...")
    top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
    commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")
    print(f"Commenter: {commenter_display_name}")

    print("Fetching channel subscriber count...")
    channel_request = youtube.channels().list(
        part="statistics",
        mine=True
    )
    channel_response = channel_request.execute()
    print("Channel statistics fetched successfully.")
    print(f"Response: {channel_response}")
    
    if not channel_response.get("items"):
        print("Could not retrieve your channel info.")
        return

    subscriber_count = channel_response["items"][0]["statistics"].get("subscriberCount", "0")
    print(f"Subscriber count: {subscriber_count}")

    new_title = f"{commenter_display_name} is my Favourite Person they helped me gain {subscriber_count} subs"
    print(f"New video title: {new_title}")

    print("Fetching video details to keep categoryId intact...")
    video_request = youtube.videos().list(
        part="snippet",
        id=VIDEO_ID
    )
    video_response = video_request.execute()
    print("Video details fetched successfully.")
    print(f"Response: {video_response}")
    
    if not video_response.get("items"):
        print("Video not found or insufficient permissions.")
        return

    category_id = video_response["items"][0]["snippet"].get("categoryId", "22")
    print(f"Video category ID: {category_id}")

    print("Updating the video title...")
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
    print(f"Success! Updated video title to: {new_title}")

except HttpError as e:
    print(f"An HTTP error occurred: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    print("Script execution completed.")
