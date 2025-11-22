"""Tests for Judge Agent."""

import pytest
from unittest.mock import Mock, AsyncMock

from src.agents.judge import JudgeAgent
from src.api.models import SkillGap, Resource, JudgementResult


@pytest.fixture
def mock_bedrock_client():
    """Create mock Bedrock client."""
    client = Mock()
    client.invoke = AsyncMock()
    return client


@pytest.fixture
def judge_agent(mock_bedrock_client):
    """Create JudgeAgent with mock client."""
    return JudgeAgent(
        mock_bedrock_client,
        relevance_threshold=0.7,
        validate_top_n=5
    )


@pytest.fixture
def sample_skill_gap():
    """Create sample skill gap."""
    return SkillGap(
        skill_name="React",
        required_level="advanced",
        priority="critical",
        recommended_starting_level="intermediate"
    )


@pytest.fixture
def sample_resources():
    """Create sample resources."""
    return [
        Resource(
            title="React Advanced Concepts",
            url="https://example.com/react-advanced",
            provider="Example",
            resource_type="course",
            difficulty_level="advanced",
            duration_hours=20,
            is_free=True,
            rating=4.8,
            description="Advanced React patterns",
            tech_stack_match=["React", "JavaScript"]
        ),
        Resource(
            title="Intro to HTML",
            url="https://example.com/html",
            provider="Example",
            resource_type="tutorial",
            difficulty_level="beginner",
            duration_hours=5,
            is_free=True,
            rating=4.0,
            description="Learn HTML basics",
            tech_stack_match=[]
        )
    ]


@pytest.mark.asyncio
async def test_validate_resources_filters_low_relevance(
    judge_agent,
    mock_bedrock_client,
    sample_skill_gap,
    sample_resources
):
    """Test that low-relevance resources are filtered out."""
    # Mock responses - first high relevance, second low relevance
    mock_bedrock_client.invoke.side_effect = [
        """{
            "resource_id": "test1",
            "is_relevant": true,
            "relevance_score": 0.9,
            "reasoning": "Excellent match",
            "recommended": true
        }""",
        """{
            "resource_id": "test2",
            "is_relevant": false,
            "relevance_score": 0.3,
            "reasoning": "Not relevant",
            "recommended": false
        }"""
    ]
    
    validated = await judge_agent.validate_resources(
        sample_skill_gap,
        sample_resources
    )
    
    # Should only keep the first resource
    assert len(validated) == 1
    assert validated[0].title == "React Advanced Concepts"


@pytest.mark.asyncio
async def test_validate_resources_empty_list(judge_agent, sample_skill_gap):
    """Test validation with empty resource list."""
    validated = await judge_agent.validate_resources(
        sample_skill_gap,
        []
    )
    
    assert len(validated) == 0


@pytest.mark.asyncio
async def test_judge_resource_successful(
    judge_agent,
    mock_bedrock_client,
    sample_skill_gap,
    sample_resources
):
    """Test successful resource judgement."""
    mock_response = """{
        "resource_id": "test",
        "is_relevant": true,
        "relevance_score": 0.85,
        "reasoning": "Good match for skill level",
        "recommended": true
    }"""
    mock_bedrock_client.invoke.return_value = mock_response
    
    from src.api.models import JudgeInput
    judge_input = JudgeInput(
        skill_gap=sample_skill_gap,
        resource=sample_resources[0]
    )
    
    judgement = await judge_agent._judge_resource(judge_input)
    
    assert isinstance(judgement, JudgementResult)
    assert judgement.is_relevant
    assert judgement.relevance_score == 0.85
    assert judgement.recommended


@pytest.mark.asyncio
async def test_validate_resources_handles_exceptions(
    judge_agent,
    mock_bedrock_client,
    sample_skill_gap,
    sample_resources
):
    """Test that validation exceptions don't break the flow."""
    # Mock to raise exception
    mock_bedrock_client.invoke.side_effect = Exception("API error")
    
    # Should still return resources despite exception
    validated = await judge_agent.validate_resources(
        sample_skill_gap,
        sample_resources
    )
    
    # Resources should be included even if validation fails
    assert len(validated) >= 1


def test_construct_prompt(judge_agent, sample_skill_gap, sample_resources):
    """Test judgement prompt construction."""
    from src.api.models import JudgeInput
    
    judge_input = JudgeInput(
        skill_gap=sample_skill_gap,
        resource=sample_resources[0]
    )
    
    prompt = judge_agent._construct_prompt(judge_input)
    
    assert "React" in prompt
    assert "advanced" in prompt
    assert "React Advanced Concepts" in prompt

