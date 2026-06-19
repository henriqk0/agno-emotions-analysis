from agno.agent import Agent
from agno.models.openrouter import OpenRouter

agent = Agent(
    model=OpenRouter(id="nvidia/nemotron-3-super-120b-a12b:free"),
    markdown=True
)

# Print the response in the terminal
agent.print_response("Share a 2 facebook comments. In end, analyse their emotions")