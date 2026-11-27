"""
Example 1: Basic Web Crawling with CrewAI
This example shows how to create a simple research assistant that crawls websites.
"""

from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools


def example_basic_crawling():
    """Basic web crawling example"""
    
    # Create tools
    tools = create_crawl4ai_tools()
    
    # Create an agent
    research_agent = Agent(
        role="Research Assistant",
        goal="Find and summarize information from websites",
        tools=tools,
        llm="gpt-4",
        verbose=True
    )
    
    # Create a task
    task = Task(
        description="Visit https://example.com and summarize what you find",
        agent=research_agent,
        expected_output="A clear summary of the website's main content"
    )
    
    # Create and run crew
    crew = Crew(
        agents=[research_agent],
        tasks=[task],
        verbose=True
    )
    
    result = crew.kickoff()
    print("Result:", result)
    
    return result


if __name__ == "__main__":
    example_basic_crawling()
