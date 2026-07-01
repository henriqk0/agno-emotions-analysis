import os

from agno.agent import Agent
from agno.skills import LocalSkills, Skills
from agno.models.openrouter import OpenRouter
from collections.abc import Sequence

# Caminho para as skills locais (ironia/sarcasmo, etc.).
# As skills estendem o comportamento do agente com instruções especializadas.
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
    """Cria instâncias de Agent com configuração padronizada.

    Uso:
        agent = AgentFactory.create_agent(
            model_id="nvidia/nemotron-3-ultra-550b-a55b:free",
            agent_instructions=[...],
            available_tools=[YouTubeCommentsTools(...)],
        )
    """

    @staticmethod
    def create_agent(
        model_id: str,
        agent_instructions: Sequence[str] = DEFAULT_INSTRUCTIONS,
        available_tools: Sequence | None = None,
    ) -> Agent:
        """Cria e retorna um agente Agno configurado.

        Args:
            model_id: Identificador do modelo no OpenRouter.
            agent_instructions: Lista de instruções de sistema para a LLM.
            available_tools: Ferramentas (Toolkit) que o agente pode usar.

        Returns:
            Instância de Agent pronta para executar.

        Raises:
            ValueError: Se model_id for vazio.
        """
        print(f"[AgentFactory] create_agent(model_id='{model_id}')")

        if not model_id.strip():
            print("[AgentFactory] ERRO: model_id vazio")
            raise ValueError("Model ID cannot be None. Please provide a valid model ID.")

        agent = Agent(
            model=OpenRouter(id=model_id),
            instructions=agent_instructions,
            tools=available_tools or [],
            markdown=True,
            skills=Skills(loaders=[LocalSkills(SKILLS_PATH)]),
        )
        print(f"[AgentFactory] Agente criado com sucesso (modelo: {model_id})")
        return agent
