from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.skills import Skills, LocalSkills
from agno.tools.reddit import RedditTools
import praw

# If using IA, document your prompts in docs/

reddit = praw.Reddit(
    client_id="my client id",
    client_secret="my client secret",
    user_agent="my user agent",
)

agent = Agent(
    model=OpenRouter(id="nvidia/nemotron-3-super-120b-a12b:free"),
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

# Print the response in the terminal
agent.print_response("Analyze the emotions expressed in the top comments of the most popular posts on r/technology today", stream=True)