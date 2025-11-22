"""Integration tests for the complete workflow."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.agents.orchestrator import OrchestratorAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.curator import CuratorAgent
from src.agents.judge import JudgeAgent
from src.api.models import AnalysisRequest, ResourceFilters, AnalysisStatus


@pytest.fixture
def mock_clients():
    """Create all mock clients."""
    bedrock = Mock()
    bedrock.invoke = AsyncMock()
    
    parallel = Mock()
    parallel.find_all = AsyncMock()
    
    return bedrock, parallel


@pytest.fixture
def orchestrator(mock_clients):
    """Create orchestrator with all agents."""
    bedrock, parallel = mock_clients
    
    analyzer = AnalyzerAgent(bedrock)
    curator = CuratorAgent(parallel, bedrock)
    judge = JudgeAgent(bedrock)
    
    return OrchestratorAgent(
        analyzer=analyzer,
        curator=curator,
        judge=judge,
        enable_judge=False,  # Disable for simpler testing
        enable_cache=False,
        enable_pii_masking=False,
        enable_notebooklm=False
    )


@pytest.mark.asyncio
async def test_end_to_end_workflow(orchestrator, mock_clients):
    """Test complete end-to-end workflow."""
    bedrock, parallel = mock_clients
    
    # Mock analyzer response
    analyzer_response = """{
        "existing_skills": [
            {
                "skill_name": "Python",
                "proficiency_level": "intermediate",
                "years_experience": 3
            }
        ],
        "skill_gaps": [
            {
                "skill_name": "Kubernetes",
                "required_level": "intermediate",
                "priority": "critical",
                "recommended_starting_level": "beginner"
            }
        ],
        "tech_stack": ["Python", "Docker"],
        "job_category": "DevOps Engineer"
    }"""
    bedrock.invoke.return_value = analyzer_response
    
    # Mock curator response
    parallel.find_all.return_value = [
        {
            "title": "Kubernetes Tutorial",
            "url": "https://example.com/k8s",
            "provider": "Example",
            "is_free": True,
            "description": "Learn Kubernetes"
        }
    ]
    
    # Create request
    request = AnalysisRequest(
        resume_text="Python developer with 3 years experience",
        job_description="Looking for DevOps engineer with Kubernetes",
        target_job_title="Senior DevOps Engineer",
        filters=ResourceFilters()
    )
    
    # Process request
    response = await orchestrator.process_request(request)
    
    # Assertions
    assert response.status == AnalysisStatus.COMPLETED
    assert response.analysis_result is not None
    assert len(response.analysis_result.skill_gaps) == 1
    assert "Kubernetes" in response.curated_resources
    assert len(response.curated_resources["Kubernetes"]) > 0


@pytest.mark.asyncio
async def test_workflow_handles_analyzer_failure(orchestrator, mock_clients):
    """Test that workflow handles analyzer failures gracefully."""
    bedrock, _ = mock_clients
    
    # Mock analyzer to fail
    bedrock.invoke.side_effect = Exception("Bedrock API error")
    
    request = AnalysisRequest(
        resume_text="Test",
        job_description="Test",
        target_job_title="Test",
        filters=ResourceFilters()
    )
    
    response = await orchestrator.process_request(request)
    
    assert response.status == AnalysisStatus.FAILED
    assert response.error_message is not None


@pytest.mark.asyncio
async def test_workflow_with_no_skill_gaps(orchestrator, mock_clients):
    """Test workflow when no skill gaps are found."""
    bedrock, _ = mock_clients
    
    # Mock response with no skill gaps
    analyzer_response = """{
        "existing_skills": [
            {
                "skill_name": "Python",
                "proficiency_level": "expert",
                "years_experience": 10
            }
        ],
        "skill_gaps": [],
        "tech_stack": ["Python"],
        "job_category": "Software Engineer"
    }"""
    bedrock.invoke.return_value = analyzer_response
    
    request = AnalysisRequest(
        resume_text="Expert Python developer",
        job_description="Python developer needed",
        target_job_title="Python Developer",
        filters=ResourceFilters()
    )
    
    response = await orchestrator.process_request(request)
    
    assert response.status == AnalysisStatus.COMPLETED
    assert len(response.analysis_result.skill_gaps) == 0
    assert len(response.curated_resources) == 0


@pytest.mark.asyncio
async def test_job_status_retrieval(orchestrator, mock_clients):
    """Test job status retrieval."""
    bedrock, parallel = mock_clients
    
    # Setup mocks
    bedrock.invoke.return_value = """{
        "existing_skills": [],
        "skill_gaps": [],
        "tech_stack": [],
        "job_category": "Unknown"
    }"""
    
    request = AnalysisRequest(
        resume_text="Test",
        job_description="Test",
        target_job_title="Test",
        filters=ResourceFilters()
    )
    
    # Process request
    response = await orchestrator.process_request(request)
    job_id = response.job_id
    
    # Retrieve status
    status = orchestrator.get_job_status(job_id)
    
    assert status is not None
    assert status.job_id == job_id
    assert status.status == AnalysisStatus.COMPLETED


def test_job_status_not_found(orchestrator):
    """Test job status for non-existent job."""
    status = orchestrator.get_job_status("nonexistent-id")
    assert status is None

