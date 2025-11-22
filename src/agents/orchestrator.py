"""Orchestrator - Coordinates autonomous multi-agent system with learning capabilities."""

import asyncio
import uuid
from typing import Dict, Optional, List
from datetime import datetime

from .analyzer import AnalyzerAgent
from .curator import CuratorAgent
from .judge import JudgeAgent
from ..integrations.redis_cache import RedisCache
from ..api.models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisResult,
    AnalysisStatus,
    Resource
)
from ..utils.logger import get_logger
from ..utils.config import get_config


logger = get_logger(__name__)


class OrchestratorAgent:
    """Meta-orchestrator that coordinates autonomous agents and learns from results."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        redis_cache: Optional[RedisCache] = None,
        enable_judge: bool = True,
        enable_cache: bool = True,
        min_quality_resources: int = 3
    ):
        """Initialize Autonomous Orchestrator.
        
        Args:
            api_key: Anthropic API key (optional, will use config if not provided)
            redis_cache: Redis cache client (optional)
            enable_judge: Whether to enable autonomous Judge validation
            enable_cache: Whether to enable Redis caching
            min_quality_resources: Minimum number of quality resources
        """
        self.config = get_config()
        self.api_key = api_key or self.config.anthropic_api_key
        
        # Initialize autonomous agents
        self.analyzer = AnalyzerAgent(api_key=self.api_key)
        self.curator = CuratorAgent(api_key=self.api_key)
        self.judge = JudgeAgent(api_key=self.api_key) if enable_judge else None
        
        self.redis_cache = redis_cache
        self.enable_judge = enable_judge
        self.enable_cache = enable_cache and redis_cache is not None
        self.min_quality_resources = min_quality_resources
        
        self.logger = logger
        
        # Learning: Track agent performance
        self.performance_metrics = {
            "analyzer": {"searches_performed": 0, "insights_generated": 0},
            "curator": {"resources_found": 0, "resources_validated": 0},
            "judge": {"tests_executed": 0, "resources_approved": 0}
        }
        
        # In-memory job tracking
        self.jobs: Dict[str, AnalysisResponse] = {}
    
    async def process_request(self, request: AnalysisRequest) -> AnalysisResponse:
        """Process request using autonomous multi-agent system.
        
        The autonomous workflow:
        1. Analyzer autonomously searches web for job requirements
        2. Curator autonomously finds and validates resource URLs
        3. Judge autonomously tests code examples
        4. Orchestrator learns from results and adapts
        
        Args:
            request: Analysis request
            
        Returns:
            Analysis response with autonomously curated resources
        """
        job_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        self.logger.info("\n" + "=" * 100)
        self.logger.info("🤖 AUTONOMOUS MULTI-AGENT ORCHESTRATOR - NEW REQUEST")
        self.logger.info("=" * 100)
        self.logger.info(f"Job ID: {job_id}")
        self.logger.info(f"Target Job: {request.target_job_title}")
        self.logger.info(f"Autonomous Agents: Analyzer (web_search) → Curator (web_search + web_fetch) → Judge (code_execution)")
        self.logger.info("=" * 100)
        
        # Initialize job tracking
        response = AnalysisResponse(
            job_id=job_id,
            status=AnalysisStatus.IN_PROGRESS,
            analysis_result=None,
            curated_resources={}
        )
        self.jobs[job_id] = response
        
        try:
            # PHASE 1: AUTONOMOUS ANALYZER
            self.logger.info("\n🔍 PHASE 1: Launching Autonomous Analyzer Agent")
            self.logger.info("   Agent will autonomously search web for job market data...\n")
            
            # Check cache first
            if self.enable_cache:
                cached_result = await self.redis_cache.get_analysis(
                    request.resume_text,
                    request.job_description
                )
                if cached_result:
                    self.logger.info("   ✅ Cache HIT - Using cached analysis\n")
                    analysis_result = cached_result
                else:
                    self.logger.info("   ❌ Cache MISS - Running autonomous analysis\n")
                    analysis_result = await self._run_analyzer(request)
            else:
                analysis_result = await self._run_analyzer(request)
            
            response.analysis_result = analysis_result
            self.performance_metrics["analyzer"]["searches_performed"] += 1
            if analysis_result.market_insights:
                self.performance_metrics["analyzer"]["insights_generated"] += 1
            
            # Cache the result
            if self.enable_cache:
                await self.redis_cache.cache_analysis(
                    request.resume_text,
                    request.job_description,
                    analysis_result
                )
            
            # PHASE 2: AUTONOMOUS CURATOR
            self.logger.info("\n📚 PHASE 2: Launching Autonomous Curator Agents")
            self.logger.info(f"   Launching {len(analysis_result.skill_gaps)} parallel curator agents...")
            self.logger.info("   Each agent will autonomously search and validate resources...\n")
            
            curated_resources = await self.curator.curate_resources(
                skill_gaps=analysis_result.skill_gaps,
                tech_stack=analysis_result.tech_stack,
                filters=request.filters
            )
            
            total_curated = sum(len(r) for r in curated_resources.values())
            self.performance_metrics["curator"]["resources_found"] += total_curated
            
            # PHASE 3: AUTONOMOUS JUDGE (if enabled)
            if self.enable_judge and self.judge:
                self.logger.info("\n⚖️  PHASE 3: Launching Autonomous Judge Agents")
                self.logger.info(f"   Agents will autonomously test code examples from resources...\n")
                
                validated_resources = {}
                for skill_name, resources in curated_resources.items():
                    if resources:
                        skill_gap = next(
                            (sg for sg in analysis_result.skill_gaps if sg.skill_name == skill_name),
                            None
                        )
                        if skill_gap:
                            validated = await self.judge.validate_resources(skill_gap, resources)
                            validated_resources[skill_name] = validated
                            
                            approved = len(validated)
                            self.performance_metrics["judge"]["resources_approved"] += approved
                        else:
                            validated_resources[skill_name] = resources
                    else:
                        validated_resources[skill_name] = []
                
                curated_resources = validated_resources
                self.performance_metrics["curator"]["resources_validated"] += sum(len(r) for r in curated_resources.values())
            
            response.curated_resources = curated_resources
            response.status = AnalysisStatus.COMPLETED
            
            # PHASE 4: LEARNING & ADAPTATION
            duration = (datetime.now() - start_time).total_seconds()
            self._learn_from_execution(analysis_result, curated_resources, duration)
            
            # Final summary
            total_final = sum(len(r) for r in curated_resources.values())
            self.logger.info("\n" + "=" * 100)
            self.logger.info("🎉 AUTONOMOUS MULTI-AGENT SYSTEM - EXECUTION COMPLETE")
            self.logger.info("=" * 100)
            self.logger.info(f"Job ID: {job_id}")
            self.logger.info(f"Duration: {duration:.2f}s")
            self.logger.info(f"Skills Analyzed: {len(analysis_result.skill_gaps)}")
            self.logger.info(f"Total Resources: {total_final}")
            self.logger.info(f"\n📊 Agent Performance:")
            self.logger.info(f"   Analyzer: {self.performance_metrics['analyzer']['searches_performed']} searches, "
                           f"{self.performance_metrics['analyzer']['insights_generated']} insights")
            self.logger.info(f"   Curator: {self.performance_metrics['curator']['resources_found']} found, "
                           f"{self.performance_metrics['curator']['resources_validated']} validated")
            if self.enable_judge:
                self.logger.info(f"   Judge: {self.performance_metrics['judge']['resources_approved']} approved after testing")
            self.logger.info("=" * 100 + "\n")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Autonomous orchestration failed: {str(e)}")
            response.status = AnalysisStatus.FAILED
            return response
    
    async def _run_analyzer(self, request: AnalysisRequest) -> AnalysisResult:
        """Run autonomous analyzer agent.
        
        Args:
            request: Analysis request
            
        Returns:
            Analysis result with market insights
        """
        from ..api.models import AnalyzerInput
        
        analyzer_input = AnalyzerInput(
            resume_text=request.resume_text,
            job_description=request.job_description,
            target_job_title=request.target_job_title
        )
        
        return await self.analyzer.analyze(analyzer_input)
    
    def _learn_from_execution(
        self,
        analysis_result: AnalysisResult,
        curated_resources: Dict[str, List[Resource]],
        duration: float
    ):
        """Learn from autonomous execution to improve future performance.
        
        This implements the "self-improving" aspect by tracking:
        - Which agents perform best
        - Resource quality patterns
        - Execution efficiency
        
        Args:
            analysis_result: Analysis result
            curated_resources: Curated resources
            duration: Execution duration in seconds
        """
        # Track efficiency
        skills_per_second = len(analysis_result.skill_gaps) / max(duration, 0.1)
        avg_resources_per_skill = sum(len(r) for r in curated_resources.values()) / max(len(curated_resources), 1)
        
        self.logger.info(f"\n📈 LEARNING METRICS:")
        self.logger.info(f"   Efficiency: {skills_per_second:.2f} skills/second")
        self.logger.info(f"   Quality: {avg_resources_per_skill:.1f} resources/skill")
        
        # Track patterns for future optimization
        # In production: store in database for ML model training
        high_priority_skills = [sg for sg in analysis_result.skill_gaps if sg.priority == "critical"]
        if high_priority_skills:
            self.logger.info(f"   Critical Skills: {len(high_priority_skills)} require immediate attention")
        
        # Identify skills with insufficient resources (for future improvement)
        insufficient = [skill for skill, resources in curated_resources.items() if len(resources) < self.min_quality_resources]
        if insufficient:
            self.logger.info(f"   ⚠️  Improvement needed for: {', '.join(insufficient)}")
    
    async def get_status(self, job_id: str) -> Optional[AnalysisResponse]:
        """Get status of an analysis job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Analysis response or None if not found
        """
        return self.jobs.get(job_id)
    
    def get_performance_metrics(self) -> Dict:
        """Get agent performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return self.performance_metrics.copy()
