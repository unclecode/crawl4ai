"""
Example 4: Data Extraction with CrewAI
This example demonstrates extracting structured data from websites.
"""

from crewai import Agent, Task, Crew
from crawl4ai import create_crawl4ai_tools


def example_data_extraction():
    """Extract structured data from websites"""
    
    tools = create_crawl4ai_tools()
    
    # Agent: Data Extraction Specialist
    data_agent = Agent(
        role="Data Extraction Specialist",
        goal="Efficiently extract and structure data from websites",
        tools=tools,
        llm="gpt-4",
        verbose=True
    )
    
    # Task: Extract specific data
    task = Task(
        description="""
        Visit a news website and extract information about the top stories.
        For each story, extract:
        1. Headline
        2. Summary/Description
        3. Publication date
        4. Author (if available)
        5. Category/Topic
        
        Format the data as a structured list.
        """,
        agent=data_agent,
        expected_output="Structured data of top news stories in JSON format"
    )
    
    # Create and run crew
    crew = Crew(
        agents=[data_agent],
        tasks=[task],
        verbose=True
    )
    
    result = crew.kickoff()
    print("Extracted Data:", result)
    
    return result


def example_multi_url_extraction():
    """Extract data from multiple URLs"""
    
    tools = create_crawl4ai_tools()
    
    # Agent: Multi-URL Data Collector
    collector_agent = Agent(
        role="Data Collection Agent",
        goal="Efficiently collect and organize data from multiple sources",
        tools=tools,
        llm="gpt-4",
        verbose=True
    )
    
    # Task: Collect from multiple sources
    task = Task(
        description="""
        Crawl information from multiple technology news sources:
        1. TechCrunch
        2. The Verge
        3. Hacker News
        
        Extract recent articles and categorize them by topic.
        Create a summary of trending topics across all sources.
        """,
        agent=collector_agent,
        expected_output="Aggregated and categorized tech news from multiple sources"
    )
    
    # Create and run crew
    crew = Crew(
        agents=[collector_agent],
        tasks=[task],
        verbose=True
    )
    
    result = crew.kickoff()
    print("Multi-Source Data:", result)
    
    return result


if __name__ == "__main__":
    print("Running Example 1: Data Extraction")
    print("=" * 50)
    example_data_extraction()
    
    print("\n\nRunning Example 2: Multi-URL Extraction")
    print("=" * 50)
    example_multi_url_extraction()
