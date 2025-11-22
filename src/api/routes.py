"""API routes for the Learning Resource Curator."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from .models import (
    AnalysisRequest,
    AnalysisResponse,
    StatusResponse,
    SkillResourcesResponse,
    FeedbackRequest,
    HealthResponse,
    AnalysisStatus
)
from ..agents.orchestrator import OrchestratorAgent
from ..utils.config import get_config


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analysis"])


# Dependency injection for orchestrator
# In production, initialize once at startup
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator instance.
    
    Returns:
        OrchestratorAgent instance
    """
    global _orchestrator
    
    if _orchestrator is None:
        # Import here to avoid circular dependencies
        from ..agents.analyzer import AnalyzerAgent
        from ..agents.curator import CuratorAgent
        from ..agents.judge import JudgeAgent
        from ..integrations.redis_cache import RedisCache
        from ..integrations.parallel_api import ParallelTaskAPI
        
        config = get_config()
        
        # Initialize clients
        
        
        parallel_api = ParallelTaskAPI(
            api_key=config.parallel_api_key,
            endpoint=config.parallel_api_endpoint,
            timeout=config.parallel_api_timeout
        )
        
        redis_cache = None
        if config.enable_cache:
            redis_cache = RedisCache(
                host=config.redis_host,
                port=config.redis_port,
                db=config.redis_db,
                password=config.redis_password,
                ttl_days=config.cache_ttl_days
            )
        
        # Initialize agents
        analyzer = AnalyzerAgent()
        curator = CuratorAgent(
            max_concurrent=config.max_concurrent_searches,
            parallel_api=parallel_api  # Pass Parallel API for resource discovery
        )
        judge = JudgeAgent(
            relevance_threshold=config.relevance_threshold
        )
        
        # Initialize orchestrator
        _orchestrator = OrchestratorAgent(
            redis_cache=redis_cache,
            enable_judge=config.enable_judge,
            enable_cache=config.enable_cache,
            min_quality_resources=config.min_quality_resources
        )
    
    return _orchestrator


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_skill_gaps(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Analyze skill gaps and curate learning resources.
    
    Args:
        request: Analysis request with resume and job description
        background_tasks: FastAPI background tasks
        orchestrator: Orchestrator agent dependency
        
    Returns:
        Analysis response with skill gaps and curated resources
    """
    try:
        logger.info("Received analysis request")
        
        # Process request (can be made async/background if needed)
        response = await orchestrator.process_request(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(
    job_id: str,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get status of an analysis job.
    
    Args:
        job_id: Job identifier
        orchestrator: Orchestrator agent dependency
        
    Returns:
        Job status and results if available
    """
    try:
        result = orchestrator.get_job_status(job_id)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Calculate progress
        progress = None
        if result.status == AnalysisStatus.IN_PROGRESS:
            progress = 50.0
        elif result.status == AnalysisStatus.COMPLETED:
            progress = 100.0
        elif result.status == AnalysisStatus.FAILED:
            progress = 0.0
        
        response = StatusResponse(
            job_id=job_id,
            status=result.status,
            progress=progress,
            message=result.error_message if result.error_message else None,
            result=result if result.status == AnalysisStatus.COMPLETED else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )


@router.get("/resources/{skill_name}", response_model=SkillResourcesResponse)
async def get_additional_resources(
    skill_name: str,
    max_results: int = 10,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get additional resources for a specific skill.
    
    Args:
        skill_name: Name of the skill
        max_results: Maximum number of resources
        orchestrator: Orchestrator agent dependency
        
    Returns:
        Additional learning resources
    """
    try:
        # This is a placeholder - implement actual logic
        raise HTTPException(
            status_code=501,
            detail="Additional resources endpoint coming soon"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get resources: {str(e)}"
        )


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on resource relevance.
    
    Args:
        request: Feedback request
        
    Returns:
        Success message
    """
    try:
        logger.info(
            f"Received feedback for {request.skill_name}: "
            f"rating={request.rating}"
        )
        
        # Store feedback (implement storage logic)
        # This could be used to improve future recommendations
        
        return {"message": "Feedback received", "job_id": request.job_id}
        
    except Exception as e:
        logger.error(f"Failed to process feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process feedback: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint.
    
    Returns:
        Service health status
    """
    config = get_config()
    
    return HealthResponse(
        status="healthy",
        version=config.app_version
    )

