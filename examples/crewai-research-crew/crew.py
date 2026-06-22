"""A small CrewAI research crew (illustrative — for `abom scan`)."""
from crewai import Agent, Crew, Task
from crewai.tools import tool
from crewai_tools import SerperDevTool


@tool("Knowledge Base Lookup")
def kb_lookup(query: str) -> str:
    """Look up internal knowledge for a query."""
    return f"kb: {query}"


researcher = Agent(
    role="Senior Researcher",
    goal="Find accurate, well-sourced facts on the topic.",
    backstory="A meticulous analyst.",
    llm="gpt-4o-mini",
    tools=[SerperDevTool(), kb_lookup],
)

writer = Agent(
    role="Report Writer",
    goal="Turn the research into a crisp brief.",
    backstory="A clear, concise writer.",
    llm="claude-3-5-sonnet-20241022",
)

research = Task(description="Research the assigned topic.", agent=researcher)
write = Task(description="Write a one-page brief.", agent=writer)

crew = Crew(agents=[researcher, writer], tasks=[research, write])
