"""Pydantic models for API request/response schemas."""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ProficiencyLevel(str, Enum):
    """Skill proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Priority(str, Enum):
    """Skill gap priority levels."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"


class ResourceType(str, Enum):
    """Types of learning resources."""
    COURSE = "course"
    TUTORIAL = "tutorial"
    DOCUMENTATION = "documentation"
    VIDEO = "video"
    BOOK = "book"
    ARTICLE = "article"


class AnalysisStatus(str, Enum):
    """Status of analysis job."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models

class ResourceFilters(BaseModel):
    """Filters for resource curation."""
    free_only: bool = Field(default=True, description="Only include free resources")
    max_duration_hours: int = Field(default=100, description="Maximum duration in hours")
    resource_types: List[ResourceType] = Field(
        default=[ResourceType.COURSE, ResourceType.TUTORIAL, ResourceType.VIDEO],
        description="Types of resources to include"
    )


class AnalysisRequest(BaseModel):
    """Request model for skill gap analysis."""
    resume_text: str = Field(..., description="Resume text content")
    job_description: str = Field(..., description="Target job description")
    target_job_title: str = Field(..., description="Title of target job role")
    filters: Optional[ResourceFilters] = Field(
        default_factory=ResourceFilters,
        description="Resource filtering preferences"
    )


class FeedbackRequest(BaseModel):
    """User feedback on resource relevance."""
    job_id: str = Field(..., description="Analysis job ID")
    skill_name: str = Field(..., description="Skill name")
    resource_url: str = Field(..., description="Resource URL")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    comments: Optional[str] = Field(None, description="Additional comments")


# Response Models

class ExistingSkill(BaseModel):
    """Model for existing skills in resume."""
    skill_name: str = Field(..., description="Name of the skill")
    proficiency_level: ProficiencyLevel = Field(..., description="Current proficiency level")
    years_experience: int = Field(..., description="Years of experience")


class SkillGap(BaseModel):
    """Model for identified skill gaps."""
    skill_name: str = Field(..., description="Name of the missing skill")
    required_level: ProficiencyLevel = Field(..., description="Required proficiency level")
    priority: Priority = Field(..., description="Priority level")
    recommended_starting_level: str = Field(..., description="Recommended starting point")


class Resource(BaseModel):
    """Model for learning resource."""
    title: str = Field(..., description="Resource title")
    url: str = Field(..., description="Resource URL")
    provider: str = Field(..., description="Content provider")
    resource_type: ResourceType = Field(..., description="Type of resource")
    difficulty_level: str = Field(..., description="Difficulty level")
    duration_hours: float = Field(..., description="Estimated duration in hours")
    is_free: bool = Field(..., description="Whether the resource is free")
    rating: Optional[float] = Field(None, description="User rating (0-5)")
    description: str = Field(..., description="Resource description")
    tech_stack_match: List[str] = Field(default_factory=list, description="Matching tech stack items")


class JudgementResult(BaseModel):
    """Model for LLM-as-a-Judge evaluation."""
    resource_id: str = Field(..., description="Resource identifier")
    is_relevant: bool = Field(..., description="Whether resource is relevant")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")
    reasoning: str = Field(..., description="Reasoning for judgement")
    recommended: bool = Field(..., description="Whether resource is recommended")


class MarketInsights(BaseModel):
    """Real-time market insights from web search."""
    demand_level: str = Field(..., description="Job market demand level")
    key_findings: List[str] = Field(default_factory=list, description="Key findings from market research")
    data_sources: List[str] = Field(default_factory=list, description="Sources of market data")


class AnalysisResult(BaseModel):
    """Model for analyzer agent output with market insights."""
    existing_skills: List[ExistingSkill] = Field(default_factory=list, description="Skills found in resume")
    skill_gaps: List[SkillGap] = Field(default_factory=list, description="Identified skill gaps")
    tech_stack: List[str] = Field(default_factory=list, description="Technology stack")
    job_category: str = Field(..., description="Job category")
    market_insights: Optional[MarketInsights] = Field(None, description="Real-time job market insights")


class AnalysisResponse(BaseModel):
    """Response model for skill gap analysis."""
    job_id: str = Field(..., description="Unique job identifier")
    status: AnalysisStatus = Field(..., description="Analysis status")
    analysis_result: Optional[AnalysisResult] = Field(None, description="Analysis results")
    curated_resources: Dict[str, List[Resource]] = Field(
        default_factory=dict,
        description="Curated resources by skill name"
    )
    notebooklm_generated: Dict[str, str] = Field(
        default_factory=dict,
        description="NotebookLM generated content by skill name"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")


class StatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: str = Field(..., description="Job identifier")
    status: AnalysisStatus = Field(..., description="Current status")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[AnalysisResponse] = Field(None, description="Result if completed")


class SkillResourcesResponse(BaseModel):
    """Response model for additional skill resources."""
    skill_name: str = Field(..., description="Skill name")
    resources: List[Resource] = Field(..., description="List of resources")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


# Internal Models (used by agents)

class AnalyzerInput(BaseModel):
    """Input model for Analyzer Agent."""
    resume_text: str
    job_description: str
    target_job_title: str


class CuratorInput(BaseModel):
    """Input model for Curator Agent."""
    skill_gap: SkillGap
    tech_stack: List[str]
    filters: ResourceFilters


class JudgeInput(BaseModel):
    """Input model for Judge Agent."""
    skill_gap: SkillGap
    resource: Resource

