"""Curator Agent - Autonomous agent that searches, validates, and curates learning resources."""

import asyncio
import json
from typing import List, Dict, Any

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
from ..api.models import CuratorInput, Resource, SkillGap, ResourceFilters, ResourceType
from ..utils.logger import get_logger
from ..utils.config import get_config


logger = get_logger(__name__)


class CuratorAgent:
    """Autonomous agent that uses web_search and web_fetch to find and validate resources."""
    
    SYSTEM_PROMPT = """You are an AUTONOMOUS learning resource curator with web search and fetch capabilities.

YOUR MISSION:
Autonomously search, validate, and curate the BEST learning resources for specific skills.

AUTONOMOUS TOOLS AVAILABLE:
- web_search: Search the web for learning resources
- web_fetch: Fetch and validate URLs to check if resources are active and high-quality

YOUR AUTONOMOUS WORKFLOW:

STEP 1: SEARCH STRATEGICALLY
- Search for "{skill_name} tutorial {level}"
- Search for "{skill_name} online course free"
- Search for "{skill_name} learning path"
- Search for "{skill_name} documentation"
- Use multiple search queries to find diverse resources

STEP 2: VALIDATE EACH RESOURCE
- Use web_fetch to validate URLs are active
- Check if content is relevant and high-quality
- Verify the resource matches the skill level
- Confirm if it's truly free (if free_only=true)

STEP 3: CURATE TOP RESOURCES
- Select only high-quality, validated resources
- Prioritize reputable sources (MDN, freeCodeCamp, Coursera, Udemy, official docs)
- Ensure variety (courses, tutorials, documentation)
- Filter out outdated or broken links

STEP 4: OUTPUT STRUCTURED JSON
Return a JSON array of resources in this format:
[
    {
        "title": "string",
        "url": "string (validated)",
        "provider": "string",
        "resource_type": "course|tutorial|documentation|video|article",
        "difficulty_level": "beginner|intermediate|advanced",
        "duration_hours": float,
        "is_free": boolean,
        "rating": float or null,
        "description": "string",
        "validation_status": "verified|active"
    }
]

REMEMBER: 
- You MUST use web_search and web_fetch tools autonomously
- Validate every URL before including it
- Only include resources you've personally verified
- Be thorough but efficient (aim for 5-10 quality resources per skill)
"""
    
    def __init__(self, api_key: str = None, max_concurrent: int = 5, parallel_api=None):
        """Initialize Autonomous Curator Agent.
        
        Args:
            api_key: Anthropic API key (optional, will use config if not provided)
            max_concurrent: Maximum concurrent skill curation tasks
            parallel_api: ParallelTaskAPI instance for resource discovery (optional)
        """
        self.config = get_config()
        self.api_key = api_key or self.config.anthropic_api_key
        self.max_concurrent = max_concurrent
        self.parallel_api = parallel_api
        self.logger = logger
    
    async def curate_resources(
        self,
        skill_gaps: List[SkillGap],
        tech_stack: List[str],
        filters: ResourceFilters
    ) -> Dict[str, List[Resource]]:
        """Autonomously curate learning resources for multiple skill gaps.
        
        Args:
            skill_gaps: List of identified skill gaps
            tech_stack: Technology stack preferences
            filters: Resource filtering criteria
            
        Returns:
            Dictionary mapping skill names to lists of validated resources
        """
        self.logger.info("=" * 80)
        self.logger.info("📚 AUTONOMOUS CURATOR AGENT - STARTING")
        self.logger.info("=" * 80)
        self.logger.info("\n📥 INPUT:")
        self.logger.info(f"Number of skill gaps: {len(skill_gaps)}")
        self.logger.info("Skills to curate (agent will autonomously search & validate):")
        for gap in skill_gaps:
            self.logger.info(f"  - {gap.skill_name}: {gap.priority} priority")
        self.logger.info(f"\nTech Stack Context: {', '.join(tech_stack[:5])}")
        self.logger.info(f"Filters: free_only={filters.free_only}, types={filters.resource_types[:3]}")
        
        # Create curation tasks for parallel execution
        tasks = []
        for skill_gap in skill_gaps:
            task = self._curate_for_skill(skill_gap, tech_stack, filters)
            tasks.append(task)
        
        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def bounded_task(coro):
            async with semaphore:
                return await coro
        
        self.logger.info(f"\n🤖 Launching {len(skill_gaps)} autonomous curator agents in parallel...")
        
        results = await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Compile results
        curated_resources = {}
        total_resources = 0
        
        for skill_gap, result in zip(skill_gaps, results):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Agent failed for {skill_gap.skill_name}: {result}")
                curated_resources[skill_gap.skill_name] = []
            else:
                curated_resources[skill_gap.skill_name] = result
                total_resources += len(result)
                self.logger.info(f"✅ {skill_gap.skill_name}: {len(result)} validated resources")
        
        self.logger.info("\n📤 AUTONOMOUS CURATION COMPLETE:")
        self.logger.info(f"Total validated resources: {total_resources} across {len(curated_resources)} skills")
        
        for skill_name, resources in curated_resources.items():
            if resources:
                self.logger.info(f"\n{skill_name}:")
                for i, resource in enumerate(resources[:3], 1):
                    self.logger.info(f"  {i}. [{resource.resource_type}] {resource.title}")
                    self.logger.info(f"     {resource.url}")
                if len(resources) > 3:
                    self.logger.info(f"  ... and {len(resources) - 3} more")
        
        self.logger.info("=" * 80 + "\n")
        
        return curated_resources
    
    async def _curate_for_skill(
        self,
        skill_gap: SkillGap,
        tech_stack: List[str],
        filters: ResourceFilters
    ) -> List[Resource]:
        """Launch autonomous agent to curate resources for a single skill.
        
        Args:
            skill_gap: Skill gap to address
            tech_stack: Technology stack context
            filters: Resource filtering criteria
            
        Returns:
            List of validated Resource objects
        """
        skill_name = skill_gap.skill_name
        level = skill_gap.recommended_starting_level
        
        self.logger.info(f"\n🤖 Launching autonomous curator for: {skill_name}")
        
        client = None
        try:
            # Initialize agent client
            client = ClaudeSDKClient()
            await client.connect()
            
            # Construct autonomous curation task
            task_prompt = self._construct_curation_task(skill_gap, tech_stack, filters)
            
            # Configure agent with tools
            options = ClaudeAgentOptions(
                system_prompt=self.SYSTEM_PROMPT.format(
                    skill_name=skill_name,
                    level=level
                ),
                permission_mode="acceptEdits",  # Allow autonomous tool use
                model=self.config.claude_model
            )
            
            # Send task to agent with options
            await client.send_message(task_prompt, options=options)
            
            # Collect agent's autonomous actions and final results
            agent_actions = []
            final_json = None
            
            async for message in client.receive_messages():
                if message.role == "assistant":
                    agent_actions.append(message)
                    
                    # Look for final JSON output
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text = block.text.strip()
                            
                            # Extract JSON from various formats
                            try:
                                # Remove markdown code blocks
                                if text.startswith("```json"):
                                    text = text[7:]
                                if text.startswith("```"):
                                    text = text[3:]
                                if text.endswith("```"):
                                    text = text[:-3]
                                text = text.strip()
                                
                                # Find and extract JSON array
                                if "[" in text:
                                    # Find the JSON array (handle text before it)
                                    start_idx = text.find("[")
                                    end_idx = text.rfind("]") + 1
                                    if start_idx >= 0 and end_idx > start_idx:
                                        json_text = text[start_idx:end_idx]
                                        parsed = json.loads(json_text)
                                        if isinstance(parsed, list) and len(parsed) > 0:
                                            final_json = parsed
                                            break
                            except json.JSONDecodeError as e:
                                self.logger.debug(f"   JSON parse error: {e}, text: {text[:100]}")
                                continue
                            except Exception as e:
                                self.logger.debug(f"   Error extracting JSON: {e}")
                                continue
                
                # Stop if we have results
                if final_json:
                    break
            
            # Disconnect
            await client.disconnect()
            
            # Log agent activity
            search_count = len([a for a in agent_actions if 'search' in str(a).lower()])
            fetch_count = len([a for a in agent_actions if 'fetch' in str(a).lower()])
            self.logger.info(f"   Agent performed: {search_count} searches, {fetch_count} validations")
            
            # Convert to Resource objects from autonomous search
            if final_json:
                resources = self._convert_to_resources(final_json, skill_gap, filters)
                self.logger.info(f"   ✅ Autonomous agents found {len(resources)} resources for {skill_name}")
                return resources
            else:
                self.logger.warning(f"   ⚠️ No valid JSON from autonomous agents for {skill_name}")
                # Try fallbacks if no resources from autonomous search
                
                # Fallback 1: Try Parallel API
                if self.parallel_api:
                    self.logger.info(f"   🔄 Fallback: Using Parallel FindAll API for {skill_name}")
                    try:
                        api_results = await self.parallel_api.search_educational_resources(
                            skill=skill_name,
                            level=skill_gap.recommended_starting_level,
                            free_only=filters.free_only,
                            max_results=10
                        )
                        resources = self._convert_to_resources(api_results, skill_gap, filters)
                        if resources:
                            self.logger.info(f"   ✅ Found {len(resources)} resources via Parallel API")
                            return resources
                    except Exception as e:
                        self.logger.warning(f"   Parallel API fallback failed: {e}")
                
                # Fallback 2: Mock resources for demo
                self.logger.info(f"   📦 Final fallback: Using mock resources for demo")
                from ..integrations.parallel_api import ParallelTaskAPI
                from ..utils.config import get_config
                if not self.parallel_api:
                    config = get_config()
                    self.parallel_api = ParallelTaskAPI(
                        api_key=config.parallel_api_key or "",
                        endpoint=config.parallel_api_endpoint
                    )
                mock_results = self.parallel_api._get_mock_resources(skill_name, skill_gap.recommended_starting_level)
                resources = self._convert_to_resources(mock_results, skill_gap, filters)
                self.logger.info(f"   ✅ Using {len(resources)} mock resources")
                return resources
            
        except Exception as e:
            self.logger.error(f"   ❌ Autonomous curation failed for {skill_name}: {e}")
            if client:
                await client.disconnect()
            
            # Don't give up - try fallbacks!
            self.logger.info(f"   🔄 Fallback: Using Parallel FindAll API for {skill_name}")
            try:
                if self.parallel_api:
                    api_results = await self.parallel_api.search_educational_resources(
                        skill=skill_name,
                        level=skill_gap.recommended_starting_level,
                        free_only=filters.free_only,
                        max_results=10
                    )
                    resources = self._convert_to_resources(api_results, skill_gap, filters)
                    if resources:
                        self.logger.info(f"   ✅ Found {len(resources)} resources via Parallel API fallback")
                        return resources
            except Exception as api_e:
                self.logger.warning(f"   Parallel API fallback also failed: {api_e}")
            
            # Final fallback to mock resources
            self.logger.info(f"   📦 Final fallback: Using mock resources for demo")
            from ..integrations.parallel_api import ParallelTaskAPI
            from ..utils.config import get_config
            if not self.parallel_api:
                config = get_config()
                self.parallel_api = ParallelTaskAPI(
                    api_key=config.parallel_api_key or "",
                    endpoint=config.parallel_api_endpoint
                )
            mock_results = self.parallel_api._get_mock_resources(skill_name, skill_gap.recommended_starting_level)
            resources = self._convert_to_resources(mock_results, skill_gap, filters)
            self.logger.info(f"   ✅ Using {len(resources)} mock resources as fallback")
            return resources
    
    def _construct_curation_task(
        self,
        skill_gap: SkillGap,
        tech_stack: List[str],
        filters: ResourceFilters
    ) -> str:
        """Construct autonomous curation task for the agent.
        
        Args:
            skill_gap: Skill gap to address
            tech_stack: Technology stack context
            filters: Resource filters
            
        Returns:
            Task prompt for agent
        """
        skill_name = skill_gap.skill_name
        level = skill_gap.recommended_starting_level
        tech_context = ", ".join(tech_stack[:3])
        
        prompt = f"""AUTONOMOUS CURATION TASK

SKILL: {skill_name}
LEVEL: {level}
PRIORITY: {skill_gap.priority}
TECH CONTEXT: {tech_context}

FILTERS:
- Free resources only: {filters.free_only}
- Max duration: {filters.max_duration_hours} hours
- Preferred types: {', '.join([t.value for t in filters.resource_types])}

YOUR AUTONOMOUS MISSION:

1. USE WEB_SEARCH to find learning resources for "{skill_name} {level}"
   - Try multiple search queries
   - Look for courses, tutorials, documentation
   - Focus on reputable sources

2. USE WEB_FETCH to validate each URL
   - Confirm the URL is active
   - Verify content quality
   - Check if it matches the skill level
   - Confirm it's free (if required)

3. CURATE 5-10 HIGH-QUALITY RESOURCES
   - Only include validated, active URLs
   - Prioritize variety (different types and sources)
   - Ensure they match the filters

4. OUTPUT JSON ARRAY
   Return ONLY the JSON array of resources (no extra text).

Begin your autonomous search and validation now!"""
        
        return prompt
    
    def _convert_to_resources(
        self,
        json_data: List[Dict[str, Any]],
        skill_gap: SkillGap,
        filters: ResourceFilters
    ) -> List[Resource]:
        """Convert agent's JSON output to Resource objects.
        
        Args:
            json_data: Agent's JSON output
            skill_gap: Original skill gap
            filters: Resource filters
            
        Returns:
            List of Resource objects
        """
        resources = []
        
        for item in json_data:
            try:
                # Skip if not a dict
                if not isinstance(item, dict):
                    continue
                
                # Validate required fields
                title = item.get("title", "").strip()
                url = item.get("url", "").strip()
                
                if not title or not url:
                    self.logger.debug(f"Skipping resource with missing title or url: {item}")
                    continue
                
                # Infer resource type
                resource_type_str = item.get("resource_type", "tutorial").lower()
                try:
                    resource_type = ResourceType(resource_type_str)
                except ValueError:
                    resource_type = ResourceType.TUTORIAL
                
                # Parse duration safely
                try:
                    duration_hours = float(item.get("duration_hours", 10.0))
                except (ValueError, TypeError):
                    duration_hours = 10.0
                
                # Create Resource object
                resource = Resource(
                    title=title,
                    url=url,
                    provider=item.get("provider", "Unknown").strip() or "Unknown",
                    resource_type=resource_type,
                    difficulty_level=item.get("difficulty_level", skill_gap.recommended_starting_level),
                    duration_hours=duration_hours,
                    is_free=bool(item.get("is_free", True)),
                    rating=item.get("rating"),
                    description=item.get("description", "").strip(),
                    tech_stack_match=[skill_gap.skill_name]
                )
                
                # Apply filters
                if filters.free_only and not resource.is_free:
                    continue
                if resource.duration_hours > filters.max_duration_hours:
                    continue
                if resource.resource_type not in filters.resource_types:
                    continue
                
                resources.append(resource)
                
            except Exception as e:
                self.logger.debug(f"Failed to convert resource {item}: {e}")
                continue
        
        return resources
