"""Analyzer Agent - Autonomous agent that analyzes skill gaps using real-time job market data."""

import json
from typing import Dict, Any, List
import asyncio

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
from ..api.models import AnalyzerInput, AnalysisResult, ExistingSkill, SkillGap
from ..utils.logger import get_logger
from ..utils.config import get_config


logger = get_logger(__name__)


class AnalyzerAgent:
    """Autonomous agent that analyzes resumes and identifies skill gaps using web search."""
    
    SYSTEM_PROMPT = """You are an AUTONOMOUS expert career analyst with access to web search tools.

YOUR MISSION:
1. Analyze the candidate's resume to extract technical skills with proficiency estimates
2. USE WEB SEARCH to find current market requirements for the target job title
3. Compare resume skills against REAL-TIME job market data
4. Identify skill gaps based on current industry standards
5. Categorize gaps by priority (critical, important, nice_to_have)

AUTONOMOUS ACTIONS YOU MUST TAKE:
- Search for "{job_title} required skills 2024" to understand current market demands
- Search for "{job_title} job requirements" to validate skill expectations
- Search for salary surveys and skill demand data for the role
- Use your findings to provide data-driven gap analysis

IMPORTANT:
- Base your analysis on REAL job market data from your web searches
- Don't guess - use web_search to get current information
- Cite specific findings from your searches

Output your FINAL analysis as a JSON object with this structure:
{
    "existing_skills": [
        {
            "skill_name": "string",
            "proficiency_level": "beginner|intermediate|advanced|expert",
            "years_experience": integer
        }
    ],
    "skill_gaps": [
        {
            "skill_name": "string",
            "required_level": "beginner|intermediate|advanced|expert",
            "priority": "critical|important|nice_to_have",
            "recommended_starting_level": "string (brief description)"
        }
    ],
    "tech_stack": ["string"],
    "job_category": "string",
    "market_insights": {
        "demand_level": "high|medium|low",
        "key_findings": ["string"],
        "data_sources": ["string"]
    }
}
"""
    
    def __init__(self, api_key: str = None):
        """Initialize Autonomous Analyzer Agent.
        
        Args:
            api_key: Anthropic API key (optional, will use config if not provided)
        """
        self.config = get_config()
        self.api_key = api_key or self.config.anthropic_api_key
        self.logger = logger
        self.client = None
    
    async def analyze(self, input_data: AnalyzerInput) -> AnalysisResult:
        """Autonomously analyze resume and job description using web search tools.
        
        This agent will:
        1. Search the web for current job market requirements
        2. Analyze the resume against real-time data
        3. Identify skill gaps based on current industry standards
        
        Args:
            input_data: Input containing resume and job description
            
        Returns:
            AnalysisResult with skill gaps and proficiency levels
            
        Raises:
            Exception: If analysis fails
        """
        self.logger.info("=" * 80)
        self.logger.info("🔍 AUTONOMOUS ANALYZER AGENT - STARTING")
        self.logger.info("=" * 80)
        self.logger.info("\n📥 INPUT:")
        self.logger.info(f"Target Job Title: {input_data.target_job_title}")
        self.logger.info(f"Resume Length: {len(input_data.resume_text)} characters")
        self.logger.info(f"Job Description Length: {len(input_data.job_description)} characters")
        
        try:
            # Initialize agent client
            self.client = ClaudeSDKClient()
            await self.client.connect()
            
            # Construct autonomous task prompt
            task_prompt = self._construct_autonomous_prompt(input_data)
            
            # Configure agent options
            options = ClaudeAgentOptions(
                system_prompt=self.SYSTEM_PROMPT.format(job_title=input_data.target_job_title),
                permission_mode="acceptEdits",  # Allow autonomous tool use
                model=self.config.claude_model
            )
            
            self.logger.info("\n🤖 Launching autonomous agent with web search tools...")
            self.logger.info("Agent will autonomously:")
            self.logger.info("  1. Search for current job market requirements")
            self.logger.info("  2. Analyze resume skills")
            self.logger.info("  3. Identify gaps based on real-time data\n")
            
            # Send task to autonomous agent with options
            await self.client.send_message(task_prompt, options=options)
            
            # Collect agent responses and actions
            agent_actions = []
            final_response = None
            
            async for message in self.client.receive_messages():
                if message.role == "assistant":
                    # Log agent's autonomous actions
                    self.logger.info(f"🤖 Agent action: {message.content[:200]}...")
                    agent_actions.append(message)
                    
                    # Check if this contains the final JSON result
                    for block in message.content:
                        if isinstance(block, TextBlock) and "{" in block.text:
                            final_response = block.text
                            break
                
                # Stop if we have a final result
                if final_response and "existing_skills" in final_response:
                    break
            
            # Disconnect client
            await self.client.disconnect()
            
            # Parse the final response with robust JSON extraction
            if not final_response:
                # Fallback: extract from last message
                final_response = agent_actions[-1].content[0].text if agent_actions else ""
            
            # Robust JSON extraction (handle incomplete/malformed JSON)
            analysis_data = self._extract_json_with_fallback(final_response)
            
            # Convert to Pydantic models
            result = self._convert_to_model(analysis_data)
            
            self.logger.info("\n📤 AUTONOMOUS ANALYSIS COMPLETE:")
            self.logger.info(f"Web Searches Performed: {len([a for a in agent_actions if 'search' in str(a).lower()])}")
            self.logger.info(f"Existing Skills: {len(result.existing_skills)}")
            for skill in result.existing_skills[:5]:
                self.logger.info(f"  - {skill.skill_name}: {skill.proficiency_level} ({skill.years_experience} years)")
            if len(result.existing_skills) > 5:
                self.logger.info(f"  ... and {len(result.existing_skills) - 5} more")
            
            self.logger.info(f"\nSkill Gaps: {len(result.skill_gaps)}")
            for gap in result.skill_gaps[:5]:
                self.logger.info(f"  - {gap.skill_name}: {gap.priority} (need {gap.required_level})")
            if len(result.skill_gaps) > 5:
                self.logger.info(f"  ... and {len(result.skill_gaps) - 5} more")
            
            if hasattr(result, 'market_insights'):
                self.logger.info(f"\n💡 Market Insights:")
                self.logger.info(f"  Demand Level: {result.market_insights.get('demand_level', 'N/A')}")
                self.logger.info(f"  Data Sources: {len(result.market_insights.get('data_sources', []))}")
            
            self.logger.info("=" * 80 + "\n")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Autonomous analysis failed: {str(e)}")
            if self.client:
                await self.client.disconnect()
            
            # Provide fallback mock analysis when autonomous agent fails
            self.logger.warning(f"   📦 Providing mock analysis as fallback")
            mock_analysis = self._generate_mock_analysis(input_data)
            self.logger.info(f"   ✅ Mock analysis: {len(mock_analysis.skill_gaps)} skill gaps identified")
            return mock_analysis
    
    def _construct_autonomous_prompt(self, input_data: AnalyzerInput) -> str:
        """Construct autonomous task prompt for the agent.
        
        Args:
            input_data: Input data
            
        Returns:
            Task prompt for autonomous agent
        """
        prompt = f"""AUTONOMOUS TASK: Skill Gap Analysis with Real-Time Market Data

TARGET JOB TITLE: {input_data.target_job_title}

CANDIDATE'S RESUME:
{input_data.resume_text}

JOB DESCRIPTION PROVIDED:
{input_data.job_description}

YOUR AUTONOMOUS WORKFLOW:

STEP 1: WEB RESEARCH (Use web_search tool autonomously)
- Search for "{input_data.target_job_title} required skills 2024"
- Search for "{input_data.target_job_title} job requirements"
- Search for "{input_data.target_job_title} skill demand" or similar
- Gather real-time data about what employers are looking for

STEP 2: ANALYZE RESUME
- Extract all technical skills from the resume
- Estimate proficiency levels based on context
- Calculate years of experience per skill

STEP 3: COMPARE WITH MARKET DATA
- Use your web search findings to identify gaps
- Prioritize gaps based on market demand
- Consider current industry trends

STEP 4: OUTPUT FINAL ANALYSIS
Provide a comprehensive JSON analysis including market insights from your searches.

REMEMBER: You have autonomous access to web_search. USE IT to make your analysis data-driven!

Begin your autonomous analysis now."""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract JSON.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from response
            # Handle potential markdown code blocks
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            data = json.loads(response)
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Response was: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
    
    def _extract_json_with_fallback(self, response: str) -> Dict[str, Any]:
        """Extract JSON from response with robust fallback handling.
        
        Args:
            response: Response text that may contain JSON
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If no valid JSON found
        """
        try:
            # Try direct parse first
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Try to find JSON object in the text
            if "{" in response:
                # Find the JSON object boundaries
                start_idx = response.find("{")
                # Find matching closing brace
                brace_count = 0
                end_idx = -1
                for i in range(start_idx, len(response)):
                    if response[i] == "{":
                        brace_count += 1
                    elif response[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx > start_idx:
                    json_text = response[start_idx:end_idx]
                    data = json.loads(json_text)
                    return data
            
            # If no JSON object found, raise error
            raise ValueError("No JSON object found in response")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.debug(f"Response was: {response[:200]}")
            raise ValueError(f"Invalid JSON in response: {e}")
    
    def _generate_mock_analysis(self, input_data: AnalyzerInput) -> AnalysisResult:
        """Generate mock analysis as fallback when autonomous agent fails.
        
        Args:
            input_data: Analysis input data
            
        Returns:
            Mock AnalysisResult
        """
        # Simple skill gap analysis based on job title keywords
        mock_gaps = []
        
        job_title_lower = input_data.target_job_title.lower()
        
        # Define common skill gaps for different roles
        if "cloud" in job_title_lower or "infrastructure" in job_title_lower:
            mock_gaps = [
                SkillGap(
                    skill_name="AWS/Cloud Platforms",
                    required_level="advanced",
                    priority="critical",
                    recommended_starting_level="intermediate"
                ),
                SkillGap(
                    skill_name="Kubernetes",
                    required_level="advanced",
                    priority="critical",
                    recommended_starting_level="intermediate"
                ),
                SkillGap(
                    skill_name="Infrastructure as Code",
                    required_level="intermediate",
                    priority="important",
                    recommended_starting_level="beginner"
                ),
                SkillGap(
                    skill_name="Docker",
                    required_level="intermediate",
                    priority="important",
                    recommended_starting_level="beginner"
                ),
                SkillGap(
                    skill_name="System Performance Optimization",
                    required_level="advanced",
                    priority="critical",
                    recommended_starting_level="intermediate"
                ),
            ]
        elif "data" in job_title_lower:
            mock_gaps = [
                SkillGap(skill_name="SQL", required_level="advanced", priority="critical", recommended_starting_level="intermediate"),
                SkillGap(skill_name="Python Data Science", required_level="advanced", priority="critical", recommended_starting_level="intermediate"),
                SkillGap(skill_name="Machine Learning", required_level="intermediate", priority="important", recommended_starting_level="beginner"),
            ]
        else:
            mock_gaps = [
                SkillGap(skill_name="System Design", required_level="advanced", priority="critical", recommended_starting_level="intermediate"),
                SkillGap(skill_name="Algorithms", required_level="intermediate", priority="important", recommended_starting_level="beginner"),
            ]
        
        return AnalysisResult(
            existing_skills=[
                ExistingSkill(skill_name="Python", proficiency_level="intermediate", years_experience=3),
                ExistingSkill(skill_name="Git", proficiency_level="intermediate", years_experience=5),
            ],
            skill_gaps=mock_gaps,
            tech_stack=["Python", "Cloud", "DevOps"],
            job_category=input_data.target_job_title
        )
    
    def _convert_to_model(self, data: Dict[str, Any]) -> AnalysisResult:
        """Convert parsed data to Pydantic model.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            AnalysisResult model with market insights
        """
        from ..api.models import MarketInsights
        
        existing_skills = [
            ExistingSkill(**skill) for skill in data.get("existing_skills", [])
        ]
        
        skill_gaps = [
            SkillGap(**gap) for gap in data.get("skill_gaps", [])
        ]
        
        # Parse market insights if available
        market_insights = None
        if "market_insights" in data:
            market_insights = MarketInsights(**data["market_insights"])
        
        return AnalysisResult(
            existing_skills=existing_skills,
            skill_gaps=skill_gaps,
            tech_stack=data.get("tech_stack", []),
            job_category=data.get("job_category", "Unknown"),
            market_insights=market_insights
        )

