"""Tests for Analyzer Agent."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.agents.analyzer import AnalyzerAgent
from src.api.models import AnalyzerInput, AnalysisResult


@pytest.fixture
def mock_bedrock_client():
    """Create mock Bedrock client."""
    client = Mock()
    client.invoke = AsyncMock()
    return client


@pytest.fixture
def analyzer_agent(mock_bedrock_client):
    """Create AnalyzerAgent with mock client."""
    return AnalyzerAgent(mock_bedrock_client)


@pytest.mark.asyncio
async def test_analyze_success(analyzer_agent, mock_bedrock_client):
    """Test successful skill gap analysis."""
    # Mock response from Bedrock
    mock_response = """
    {
        "existing_skills": [
            {
                "skill_name": "Python",
                "proficiency_level": "intermediate",
                "years_experience": 3
            }
        ],
        "skill_gaps": [
            {
                "skill_name": "React",
                "required_level": "advanced",
                "priority": "critical",
                "recommended_starting_level": "Start with React fundamentals and hooks"
            }
        ],
        "tech_stack": ["Python", "Flask"],
        "job_category": "Software Engineer"
    }
    """
    mock_bedrock_client.invoke.return_value = mock_response
    
    # Create input
    input_data = AnalyzerInput(
        resume_text="Python developer with 3 years experience",
        job_description="Looking for React developer",
        target_job_title="Senior Frontend Engineer"
    )
    
    # Analyze
    result = await analyzer_agent.analyze(input_data)
    
    # Assertions
    assert isinstance(result, AnalysisResult)
    assert len(result.existing_skills) == 1
    assert result.existing_skills[0].skill_name == "Python"
    assert len(result.skill_gaps) == 1
    assert result.skill_gaps[0].skill_name == "React"
    assert result.job_category == "Software Engineer"
    
    # Verify Bedrock was called
    mock_bedrock_client.invoke.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_invalid_json(analyzer_agent, mock_bedrock_client):
    """Test handling of invalid JSON response."""
    mock_bedrock_client.invoke.return_value = "Invalid JSON response"
    
    input_data = AnalyzerInput(
        resume_text="Test resume",
        job_description="Test job",
        target_job_title="Test Job"
    )
    
    with pytest.raises(ValueError):
        await analyzer_agent.analyze(input_data)


@pytest.mark.asyncio
async def test_analyze_with_markdown_code_block(analyzer_agent, mock_bedrock_client):
    """Test parsing response with markdown code blocks."""
    mock_response = """```json
    {
        "existing_skills": [],
        "skill_gaps": [],
        "tech_stack": [],
        "job_category": "Unknown"
    }
    ```"""
    mock_bedrock_client.invoke.return_value = mock_response
    
    input_data = AnalyzerInput(
        resume_text="Test",
        job_description="Test",
        target_job_title="Test"
    )
    
    result = await analyzer_agent.analyze(input_data)
    assert isinstance(result, AnalysisResult)


def test_construct_prompt(analyzer_agent):
    """Test prompt construction."""
    input_data = AnalyzerInput(
        resume_text="My resume",
        job_description="Job requirements",
        target_job_title="Engineer"
    )
    
    prompt = analyzer_agent._construct_prompt(input_data)
    
    assert "Engineer" in prompt
    assert "My resume" in prompt
    assert "Job requirements" in prompt

