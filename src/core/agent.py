
import os

from agno.agent import Agent
from agno.skills import LocalSkills, Skills
from agno.models.openrouter import OpenRouter
from collections.abc import Sequence

SKILLS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".claude",
    "skills",
)

# If not given any instructions...
DEFAULT_INSTRUCTIONS = (
    "Answer like a panda.",
)

class AgentFactory:

    @staticmethod
    def create_agent(
        model_id: str,
        agent_instructions: Sequence[str] = DEFAULT_INSTRUCTIONS,
        available_tools: Sequence | None = None,
    ) -> Agent:

        if not model_id.strip():
            raise ValueError("Model ID cannot be None. Please provide a valid model ID.")
        
        return Agent(
            model = OpenRouter(id=model_id),
            instructions = agent_instructions,
            tools = available_tools or [],
            markdown = True,
            skills = Skills(loaders = [LocalSkills(SKILLS_PATH)])
        )
    