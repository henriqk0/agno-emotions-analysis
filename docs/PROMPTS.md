# Most important Prompts used

# Prompt 1 - Transpose current reddit craw to fetch youtube comments

## Input

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.skills import Skills, LocalSkills
from agno.tools.reddit import RedditTools
import praw
reddit = praw.Reddit(
client_id="my client id",
client_secret="my client secret",
user_agent="my user agent",
)
agent = Agent(
model=OpenRouter(id="poolside/laguna-m.1:free"),
instructions=[
"You are a Reddit content analyst that helps explore and understand Reddit data",
"Browse subreddits, analyze posts, and provide insights about discussions",
"Respect Reddit's community guidelines and rate limits",
"Provide clear summaries of Reddit content and trends",
],
tools=[RedditTools(reddit_instance=reddit)],
markdown=True,
skills=Skills(loaders=[LocalSkills("/.claude/skills")])
)
agent.print_response("Analyze the emotions expressed in the top comments of the most popular posts on r/technology today", stream=True)

Exist some equivalent to this, but for youtube commentaries?

## Output (CLAUDE (free, via WEB))

Short answer: not really, not as a drop-in toolkit. Agno's built-in YouTubeTools only wraps youtube_transcript_api for captions, video metadata, and timestamps — it has no comment-fetching method at all, so it's not the comment-analysis equivalent of RedditTools.
The actual equivalent to "praw + RedditTools" for YouTube is the official YouTube Data API v3 (via google-api-python-client), which has a commentThreads().list() endpoint. There's no pre-built Agno toolkit for it yet, but writing one is exactly the same pattern as wrapping praw — here's a working version:
pythonimport json
from googleapiclient.discovery import build
from agno.tools import Toolkit

class YouTubeCommentsTools(Toolkit):
def **init**(self, api_key: str, **kwargs):
self.youtube = build("youtube", "v3", developerKey=api_key)
tools = [self.search_videos, self.get_video_comments]
super().**init**(name="youtube_comments_tools", tools=tools, **kwargs)

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

Then wire it up exactly like your Reddit example:
pythonfrom agno.agent import Agent
from agno.models.openrouter import OpenRouter

agent = Agent(
model=OpenRouter(id="poolside/laguna-m.1:free"),
instructions=[
"You are a YouTube content analyst that helps explore and understand YouTube data",
"Search for popular videos, fetch their top comments, and analyze sentiment/emotion",
"Respect YouTube's API quota and terms of service",
"Provide clear summaries of comment trends and audience reactions",
],
tools=[YouTubeCommentsTools(api_key="YOUR_YOUTUBE_DATA_API_KEY")],
markdown=True,
)

agent.print_response(
"Analyze the emotions expressed in the top comments of the most popular AI videos today",
stream=True,
)
A few practical notes:

Get the API key: enable "YouTube Data API v3" in Google Cloud Console and create an API key — no OAuth needed for read-only public comment access.
Install: pip install google-api-python-client.
Quota: default is 10,000 units/day. search.list costs 100 units per call, commentThreads.list costs 1 unit — so searching is the expensive part, comment-fetching is cheap.
Comments-disabled videos will throw an error from the API; the toolkit above catches that and returns a message instead of crashing.
You can combine this with the built-in YouTubeTools in the same agent — one for transcripts/metadata, this one for comments — to get full video+audience analysis in a single agent.

If you'd rather not manage Google API quotas yourself, there are also paid scraping APIs (e.g. Apify's YouTube actors, which already have an official Agno integration via ApifyTools) that return comments without needing a Google Cloud key — but the official Data API is the closest direct analog to what praw/RedditTools gives you

# Prompt 2 - Transpose current frontend chatbot craw to only pass youtube content to fetch comments

## Input

Please review my `main.py` and adapt the Reflex frontend (within `src/chat`) so that the chat sends only the input passed to `print_response`. The `print_response` function will generate the AI's output for the chat, and the UI should display a user-friendly indicator that processing is underway while it loads.

## Output (Opencode w/ Big Pickle)

- adaptations to call agno

# Prompt 3 - Fix rxconfig.py app_name

## Input

how to change rxconfig app_name in accord with current code structure?

## Output (Opencode w/ Big Pickle)

- app_name fix

# Prompt 4 - Create irony and sarcasm .md

## Input resume

Fill the SKILL.md (or the agno skill format) to one LLM have a better sarcasm and irony understand

## Output (Opencode w/ Big Pickle)

- the .claude/irony-and-sarcasm/SKILL.md following agno skill pattern, that starts with:

---

name: irony-and-sarcasm
description: >
Helps detect sarcasm, irony, and satirical tone in YouTube comments, since
these are often misclassified by sentiment/emotion analysis models.

---
