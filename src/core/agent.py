import os
from collections.abc import Sequence

from agno.agent import Agent
from agno.models.sambanova import Sambanova
from agno.skills import LocalSkills, Skills

SKILLS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    ".claude",
    "skills",
)

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
        print(f"[AgentFactory] create_agent(model_id='{model_id}')")

        if not model_id.strip():
            print("[AgentFactory] ERRO: model_id vazio")
            raise ValueError("Model ID cannot be None. Please provide a valid model ID.")

        agent = Agent(
            model=Sambanova(id=model_id),
            instructions=agent_instructions,
            tools=available_tools or [],
            skills=Skills(loaders=[LocalSkills(SKILLS_PATH)]),
        )
        print(f"[AgentFactory] Agente criado com sucesso (modelo: {model_id})")
        return agent
