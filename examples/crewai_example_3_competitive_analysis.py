"""
Example 3: Competitive Analysis with CrewAI
This example shows how to use multiple crawls to gather and analyze competitive data.
"""

from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools


def example_competitive_analysis():
    """Competitive analysis using web crawling"""
    
    tools = create_crawl4ai_tools()
    
    # Agent 1: Competitive Intelligence Gatherer
    intelligence_agent = Agent(
        role="Competitive Intelligence Specialist",
        goal="Gather detailed information about competitors and their offerings",
        tools=tools,
        llm="gpt-4",
        verbose=True
    )
    
    # Agent 2: Competitive Analyst
    analysis_agent = Agent(
        role="Competition Analyst",
        goal="Analyze competitive positioning and recommend strategies",
        tools=[],
        llm="gpt-4",
        verbose=True
    )
    
    # Task 1: Gather competitor information
    gather_task = Task(
        description="""
        Crawl and analyze the websites of major competitors in the tech industry.
        Focus on:
        1. Product offerings and features
        2. Pricing strategies
        3. Target market positioning
        4. Recent announcements or news
        
        Compare at least 3 major competitors.
        """,
        agent=intelligence_agent,
        expected_output="Detailed competitive intelligence report"
    )
    
    # Task 2: Analyze and provide recommendations
    analysis_task = Task(
        description="""
        Based on the competitive intelligence:
        1. Create a comparison matrix
        2. Identify market gaps and opportunities
        3. Recommend positioning strategies
        4. Suggest competitive differentiators
        """,
        agent=analysis_agent,
        expected_output="Strategic competitive analysis with recommendations",
        context=[gather_task]
    )
    
    # Create and run crew
    crew = Crew(
        agents=[intelligence_agent, analysis_agent],
        tasks=[gather_task, analysis_task],
        verbose=True
    )
    
    result = crew.kickoff()
    print("Competitive Analysis Result:", result)
    
    return result


if __name__ == "__main__":
    example_competitive_analysis()
