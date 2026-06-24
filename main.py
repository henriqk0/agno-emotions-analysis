# Same functionality of src/chat/components/state.py, but working only via terminal 

# After install requirements, if you want run reflex
# Go to terminal and:
# 1. Initialize Reflex
#    run: reflex init
# 2. Build frontend
#    run: reflex export

import os

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.skills import LocalSkills, Skills
from dotenv import load_dotenv

from src.core.YoutubeCommentTools import YouTubeCommentsTools

load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_DATA_API_KEY")

agent = Agent(
    model=OpenRouter(id="poolside/laguna-m.1:free"),
    instructions=[
        "You are a YouTube content analyst that helps explore and understand YouTube data",
        "Search for popular videos, fetch their top comments, and analyze sentiment/emotion",
        "Respect YouTube's API quota and terms of service",
        "Provide clear summaries of comment trends and audience reactions",
    ],
    tools=[YouTubeCommentsTools(api_key=youtube_api_key)],
    markdown=True,
    skills=Skills(loaders=[LocalSkills(os.path.join(os.path.dirname(__file__), ".claude", "skills"))]),
)

if __name__ == "__main__":
    user_input = input()

    agent.print_response(
        f"Analyze the emotions expressed in the top comments of the most popular {user_input} videos",
        stream=True,
    )