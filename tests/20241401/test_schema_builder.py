# https://claude.ai/chat/c4bbe93d-fb54-44ce-92af-76b4c8086c6b
# https://claude.ai/chat/c24a768c-d8b2-478a-acc7-d76d42a308da
import json
import os
import sys
from typing import Optional

import pytest

from crawl4ai import LLMConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Test HTML - A complex job board with companies, departments, and positions
test_html = """
<div class="company-listings">
    <div class="company" data-company-id="123">
        <div class="company-header">
            <img class="company-logo" src="google.png" alt="Google">
            <h1 class="company-name">Google</h1>
            <div class="company-meta">
                <span class="company-size">10,000+ employees</span>
                <span class="company-industry">Technology</span>
                <a href="https://google.careers" class="careers-link">Careers Page</a>
            </div>
        </div>

        <div class="departments">
            <div class="department">
                <h2 class="department-name">Engineering</h2>
                <div class="positions">
                    <div class="position-card" data-position-id="eng-1">
                        <h3 class="position-title">Senior Software Engineer</h3>
                        <span class="salary-range">$150,000 - $250,000</span>
                        <div class="position-meta">
                            <span class="location">Mountain View, CA</span>
                            <span class="job-type">Full-time</span>
                            <span class="experience">5+ years</span>
                        </div>
                        <div class="skills-required">
                            <span class="skill">Python</span>
                            <span class="skill">Kubernetes</span>
                            <span class="skill">Machine Learning</span>
                        </div>
                        <p class="position-description">Join our core engineering team...</p>
                        <div class="application-info">
                            <span class="posting-date">Posted: 2024-03-15</span>
                            <button class="apply-btn" data-req-id="REQ12345">Apply Now</button>
                        </div>
                    </div>
                    <!-- More positions -->
                </div>
            </div>

            <div class="department">
                <h2 class="department-name">Marketing</h2>
                <div class="positions">
                    <div class="position-card" data-position-id="mkt-1">
                        <h3 class="position-title">Growth Marketing Manager</h3>
                        <span class="salary-range">$120,000 - $180,000</span>
                        <div class="position-meta">
                            <span class="location">New York, NY</span>
                            <span class="job-type">Full-time</span>
                            <span class="experience">3+ years</span>
                        </div>
                        <div class="skills-required">
                            <span class="skill">SEO</span>
                            <span class="skill">Analytics</span>
                            <span class="skill">Content Strategy</span>
                        </div>
                        <p class="position-description">Drive our growth initiatives...</p>
                        <div class="application-info">
                            <span class="posting-date">Posted: 2024-03-14</span>
                            <button class="apply-btn" data-req-id="REQ12346">Apply Now</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
"""


@pytest.fixture
def config() -> LLMConfig:
    """Load OpenAI API key from environment variable.

    If the API key is not found, skip the test."""
    api_token: Optional[str] = os.environ.get("OPENAI_API_KEY")
    if not api_token:
        pytest.skip("OpenAI API key is required for this test")

    return LLMConfig(api_token=api_token)


def test_no_query_full_schema(config: LLMConfig):
    """No query (should extract everything)"""
    schema1 = JsonCssExtractionStrategy.generate_schema(test_html, llm_config=config)
    print(json.dumps(schema1, indent=2))


def test_basic_job_info(config: LLMConfig):
    """Query for just basic job info"""
    query2 = "I only need job titles, salaries, and locations"
    schema2 = JsonCssExtractionStrategy.generate_schema(test_html, query2, llm_config=config)
    print(json.dumps(schema2, indent=2))


def test_company_and_department_structure(config: LLMConfig):
    """Query for company and department structure"""
    query3 = "Extract company details and department names, without position details"
    schema3 = JsonCssExtractionStrategy.generate_schema(test_html, query3, llm_config=config)
    print(json.dumps(schema3, indent=2))


def test_specific_skills_tracking(config: LLMConfig):
    """Query for specific skills tracking"""
    query4 = "I want to analyze required skills across all positions"
    schema4 = JsonCssExtractionStrategy.generate_schema(test_html, query4, llm_config=config)
    print(json.dumps(schema4, indent=2))


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", "-v", str(__file__)]))
