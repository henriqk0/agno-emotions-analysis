# Same functionality of src/chat/components/state.py, but working only via terminal

# After install requirements, if you want run reflex
# Go to terminal and:
## 1. Initialize Reflex
#     reflex init
## 2. Build frontend
#    reflex export
## Or, only:
#    reflex run


import os

from agno.agent import Agent
from agno.models.sambanova import Sambanova
from agno.skills import LocalSkills, Skills
from dotenv import load_dotenv

from core.youtube_comment_tools import YouTubeCommentsTools

load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_DATA_API_KEY")
sambanova_api_key = os.getenv("SAMBANOVA_API_KEY")

agent = Agent(
    model=Sambanova(
        id="gemma-4-31B-it",
        api_key=sambanova_api_key,
    ),
    instructions=[
        "You are a YouTube content analyst that helps explore and understand YouTube data",
        "Search for popular videos, fetch their top comments, and analyze sentiment/emotion",
        "Respect YouTube's API quota and terms of service",
        "Provide clear summaries of comment trends and audience reactions",
    ],
    tools=[YouTubeCommentsTools(api_key=youtube_api_key)],
    markdown=True,
    skills=Skills(
        loaders=[
            LocalSkills(
                os.path.join(os.path.dirname(__file__), ".claude", "skills")
            )
        ]
    ),
)

if __name__ == "__main__":
    user_input = input()

    agent.print_response(
        f"Analyze the emotions expressed in the top comments of the most popular {user_input} videos",
        stream=True,
    )