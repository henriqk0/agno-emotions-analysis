import json
from googleapiclient.discovery import build
from agno.tools import Toolkit

class YouTubeCommentsTools(Toolkit):
    def __init__(self, api_key: str, **kwargs):
        self.youtube = build("youtube", "v3", developerKey=api_key)
        tools = [self.search_videos, self.get_video_comments]
        super().__init__(name="youtube_comments_tools", tools=tools, **kwargs)

    def search_videos(self, query: str, max_results: int = 5, order: str = "viewCount") -> str:
        """Search YouTube videos by query, ordered by popularity (viewCount/relevance/date/rating)."""
        res = self.youtube.search().list(
            part="snippet", q=query, type="video", order=order, maxResults=max_results
        ).execute()
        videos = [
            {"video_id": i["id"]["videoId"], "title": i["snippet"]["title"], "channel": i["snippet"]["channelTitle"]}
            for i in res.get("items", [])
        ]
        return json.dumps(videos, indent=2)

    def get_video_comments(self, video_id: str, max_results: int = 50, order: str = "relevance") -> str:
        """Fetch top-level comments for a video, ordered by relevance or time."""
        try:
            res = self.youtube.commentThreads().list(
                part="snippet", videoId=video_id, maxResults=max_results,
                order=order, textFormat="plainText"
            ).execute()
        except Exception as e:
            return f"Error fetching comments (comments may be disabled): {e}"

        comments = [
            {
                "author": c["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                "text": c["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                "likes": c["snippet"]["topLevelComment"]["snippet"]["likeCount"],
                "published_at": c["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
            }
            for c in res.get("items", [])
        ]
        return json.dumps(comments, indent=2)