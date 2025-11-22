"""Tests for Curator Agent."""

import pytest
from unittest.mock import Mock, AsyncMock

from src.agents.curator import CuratorAgent
from src.api.models import SkillGap, ResourceFilters, Resource


@pytest.fixture
def mock_parallel_api():
    """Create mock Parallel Task API."""
    api = Mock()
    api.find_all = AsyncMock()
    return api


@pytest.fixture
def mock_bedrock_client():
    """Create mock Bedrock client."""
    client = Mock()
    client.invoke = AsyncMock()
    return client


@pytest.fixture
def curator_agent(mock_parallel_api, mock_bedrock_client):
    """Create CuratorAgent with mocks."""
    return CuratorAgent(
        mock_parallel_api,
        mock_bedrock_client,
        timeout=30,
        max_concurrent=5
    )


@pytest.mark.asyncio
async def test_curate_resources_single_skill(curator_agent, mock_parallel_api):
    """Test curating resources for a single skill."""
    # Mock API response
    mock_parallel_api.find_all.return_value = [
        {
            "title": "React Tutorial",
            "url": "https://example.com/react",
            "provider": "Example",
            "is_free": True,
            "rating": 4.5,
            "description": "Learn React"
        }
    ]
    
    skill_gaps = [
        SkillGap(
            skill_name="React",
            required_level="advanced",
            priority="critical",
            recommended_starting_level="intermediate"
        )
    ]
    
    filters = ResourceFilters(
        free_only=True,
        max_duration_hours=100,
        resource_types=["course", "tutorial", "video"]
    )
    
    result = await curator_agent.curate_resources(
        skill_gaps=skill_gaps,
        tech_stack=["JavaScript"],
        filters=filters
    )
    
    assert "React" in result
    assert len(result["React"]) > 0
    assert isinstance(result["React"][0], Resource)
    mock_parallel_api.find_all.assert_called_once()


@pytest.mark.asyncio
async def test_curate_resources_multiple_skills(curator_agent, mock_parallel_api):
    """Test curating resources for multiple skills in parallel."""
    mock_parallel_api.find_all.return_value = [
        {
            "title": "Tutorial",
            "url": "https://example.com",
            "provider": "Example",
            "is_free": True
        }
    ]
    
    skill_gaps = [
        SkillGap(
            skill_name="React",
            required_level="advanced",
            priority="critical",
            recommended_starting_level="intermediate"
        ),
        SkillGap(
            skill_name="Docker",
            required_level="intermediate",
            priority="important",
            recommended_starting_level="beginner"
        )
    ]
    
    filters = ResourceFilters()
    
    result = await curator_agent.curate_resources(
        skill_gaps=skill_gaps,
        tech_stack=[],
        filters=filters
    )
    
    assert "React" in result
    assert "Docker" in result
    assert mock_parallel_api.find_all.call_count == 2


def test_build_search_query(curator_agent):
    """Test search query building."""
    from src.api.models import CuratorInput
    
    curator_input = CuratorInput(
        skill_gap=SkillGap(
            skill_name="Kubernetes",
            required_level="intermediate",
            priority="critical",
            recommended_starting_level="beginner"
        ),
        tech_stack=["Docker", "AWS"],
        filters=ResourceFilters(free_only=True)
    )
    
    query = curator_agent._build_search_query(curator_input)
    
    assert "Kubernetes" in query
    assert "beginner" in query
    assert "free" in query


def test_infer_resource_type(curator_agent):
    """Test resource type inference."""
    video_result = {"url": "https://youtube.com/watch", "title": "Video Tutorial"}
    assert curator_agent._infer_resource_type(video_result) == "video"
    
    course_result = {"url": "https://udemy.com/course", "title": "Complete Course"}
    assert curator_agent._infer_resource_type(course_result) == "course"
    
    docs_result = {"url": "https://docs.example.com", "title": "Documentation"}
    assert curator_agent._infer_resource_type(docs_result) == "documentation"

