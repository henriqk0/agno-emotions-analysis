from core.agent import AgentFactory
from core.youtube_comment_tools import YouTubeCommentsTools
from core.settings import AGENT_INSTRUCTIONS

import os
from dotenv import load_dotenv

load_dotenv()

youtube_api_key = os.getenv("YOUTUBE_DATA_API_KEY")


class AgentService:

    @staticmethod
    async def run(question: str, model_id: str):
        agent = AgentFactory.create_agent(
            model_id=model_id,
            agent_instructions=AGENT_INSTRUCTIONS,
            available_tools=[YouTubeCommentsTools(api_key=youtube_api_key)]
        )

        prompt = f"Analyze the emotions expressed in the top comments of the most popular {question} videos"

        for chunk in agent.run(prompt, stream=True):
            if chunk.content:
                yield chunk.content
