"""
Example 2: Multi-Agent Research Workflow with CrewAI
This example demonstrates how multiple agents can work together:
one to crawl websites, one to analyze the data.
"""

from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools


def example_multi_agent_research():
    """Multi-agent research workflow"""
    
    tools = create_crawl4ai_tools()
    
    # Agent 1: Researcher - gathers information
    researcher = Agent(
        role="Research Specialist",
        goal="Find comprehensive information on assigned topics",
        tools=tools,
        llm="gpt-4",
        verbose=True
    )
    
    # Agent 2: Analyst - analyzes findings
    analyst = Agent(
        role="Data Analyst",
        goal="Synthesize research into actionable insights",
        tools=[],  # No tools needed, uses researcher's output
        llm="gpt-4",
        verbose=True
    )
    
    # Task 1: Research
    research_task = Task(
        description="""
        Research the latest developments in artificial intelligence.
        Visit multiple authoritative sources and gather comprehensive information.
        """,
        agent=researcher,
        expected_output="Detailed findings on latest AI developments"
    )
    
    # Task 2: Analysis
    analysis_task = Task(
        description="""
        Analyze the researched information and identify:
        1. Key trends in AI development
        2. Major innovations
        3. Market implications
        """,
        agent=analyst,
        expected_output="Strategic analysis with trend identification",
        context=[research_task]  # Use output from research_task
    )
    
    # Create and run crew
    crew = Crew(
        agents=[researcher, analyst],
        tasks=[research_task, analysis_task],
        verbose=True
    )
    
    result = crew.kickoff()
    print("Final Result:", result)
    
    return result


if __name__ == "__main__":
    example_multi_agent_research()
