"""Pytest configuration and shared fixtures."""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_resume():
    """Sample resume text for testing."""
    return """
John Doe
Software Engineer

EXPERIENCE:
Senior Software Engineer at TechCorp (2021-2024)
- Developed microservices using Python and Flask
- Managed PostgreSQL databases
- Implemented REST APIs
- Used Docker for containerization

Junior Developer at StartupXYZ (2019-2021)
- Built web applications with JavaScript and jQuery
- Worked with Git for version control
- Basic Linux administration

SKILLS:
- Programming: Python, JavaScript, SQL
- Frameworks: Flask, jQuery
- Databases: PostgreSQL, MySQL
- Tools: Git, Docker, Linux
- Proficiency: Intermediate in Python, Beginner in JavaScript

EDUCATION:
BS Computer Science, State University (2019)
"""


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
Senior Full Stack Engineer

REQUIREMENTS:
- 5+ years of software development experience
- Expert proficiency in React and Node.js
- Strong experience with AWS cloud services
- Kubernetes and Docker orchestration
- CI/CD pipeline setup and maintenance
- TypeScript for type-safe development
- Microservices architecture design
- Experience with Redis caching
- GraphQL API development

NICE TO HAVE:
- Terraform for infrastructure as code
- Experience with serverless architectures
- MongoDB or other NoSQL databases
- React Native for mobile development

This role requires strong problem-solving skills and ability to work in a fast-paced environment.
"""


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result for testing."""
    from src.api.models import AnalysisResult, ExistingSkill, SkillGap
    
    return AnalysisResult(
        existing_skills=[
            ExistingSkill(
                skill_name="Python",
                proficiency_level="intermediate",
                years_experience=5
            ),
            ExistingSkill(
                skill_name="Docker",
                proficiency_level="beginner",
                years_experience=2
            )
        ],
        skill_gaps=[
            SkillGap(
                skill_name="React",
                required_level="expert",
                priority="critical",
                recommended_starting_level="intermediate"
            ),
            SkillGap(
                skill_name="Kubernetes",
                required_level="advanced",
                priority="critical",
                recommended_starting_level="beginner"
            ),
            SkillGap(
                skill_name="AWS",
                required_level="advanced",
                priority="important",
                recommended_starting_level="intermediate"
            )
        ],
        tech_stack=["Python", "JavaScript", "Docker"],
        job_category="Software Engineer"
    )

