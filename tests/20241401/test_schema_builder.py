# https://claude.ai/chat/c4bbe93d-fb54-44ce-92af-76b4c8086c6b
# https://claude.ai/chat/c24a768c-d8b2-478a-acc7-d76d42a308da
import json
import os
import sys
from typing import Any, Optional

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
    schema = JsonCssExtractionStrategy.generate_schema(test_html, llm_config=config)
    assert schema
    assert isinstance(schema, dict)
    assert schema.get("name", "")
    fields: list[dict[str, Any]] = schema.get("fields", [])
    assert len(fields) == 6
    seen_positions: bool = False
    for field in fields:
        assert isinstance(field, dict)
        if field.get("name", "") == "departments":
            department_fields: list[dict[str, Any]] = field.get("fields", [])
            assert len(department_fields) == 2
            for department_field in department_fields:
                assert isinstance(department_field, dict)
                if department_field.get("name", "") == "positions":
                    position_fields: list[dict[str, Any]] = department_field.get("fields", [])
                    assert len(position_fields) > 8
                    seen_positions = True
    assert seen_positions


@pytest.mark.skip(reason="LLM extraction can be unpredictable")
def test_basic_job_info(config: LLMConfig):
    """Query for just basic job info"""
    query = "I only need job titles, salaries, and locations"
    schema = JsonCssExtractionStrategy.generate_schema(test_html, query=query, llm_config=config)
    print(json.dumps(schema, indent=2))
    assert schema
    assert isinstance(schema, dict)
    assert schema.get("name", "")
    fields: list[dict[str, Any]] = schema.get("fields", [])
    assert len(fields) == 3
    seen_job_title: bool = False
    seen_salary_range: bool = False
    seen_location: bool = False
    for field in fields:
        assert isinstance(field, dict)
        name: str = field.get("name", "")
        if name == "job_title":
            seen_job_title = True
        elif name == "salary_range":
            seen_salary_range = True
        elif name == "location":
            seen_location = True

    assert seen_job_title
    assert seen_salary_range
    assert seen_location


def test_company_and_department_structure(config: LLMConfig):
    """Query for company and department structure"""
    query = "Extract company details and department names, without position details"
    schema = JsonCssExtractionStrategy.generate_schema(test_html, query=query, llm_config=config)
    print(json.dumps(schema, indent=2))
    assert schema
    assert isinstance(schema, dict)
    assert schema.get("name", "")
    fields: list[dict[str, Any]] = schema.get("fields", [])
    assert len(fields) == 6
    seen_department_name: bool = False
    for field in fields:
        assert isinstance(field, dict)
        if field.get("name", "") == "departments":
            department_fields: list[dict[str, Any]] = field.get("fields", [])
            assert len(department_fields) == 1
            for department_field in department_fields:
                assert isinstance(department_field, dict)
                if department_field.get("name", "") == "department_name":
                    seen_department_name = True
    assert seen_department_name


@pytest.mark.skip(reason="LLM extraction can be unpredictable")
def test_specific_skills_tracking(config: LLMConfig):
    """Query for specific skills tracking"""
    query = "I want to analyze required skills across all positions"
    schema = JsonCssExtractionStrategy.generate_schema(test_html, query=query, llm_config=config)
    print(json.dumps(schema, indent=2))
    assert schema
    assert isinstance(schema, dict)
    assert schema.get("name", "")
    fields: list[dict[str, Any]] = schema.get("fields", [])
    seen_skills_required: bool = False
    for field in fields:
        assert isinstance(field, dict)
        if field.get("name", "") == "departments":
            department_fields: list[dict[str, Any]] = field.get("fields", [])
            assert len(department_fields) == 2
            for department_field in department_fields:
                assert isinstance(department_field, dict)
                if department_field.get("name", "") == "positions":
                    position_fields: list[dict[str, Any]] = department_field.get("fields", [])
                    assert len(position_fields)
                    for position_field in position_fields:
                        assert isinstance(position_field, dict)
                        if position_field.get("name", "") == "skills_required":
                            seen_skills_required = True
    assert seen_skills_required


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))
