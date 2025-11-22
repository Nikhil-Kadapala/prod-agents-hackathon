"""Judge Agent - Autonomous validator that tests resources with code execution."""

import json
from typing import List, Dict, Any
import asyncio

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock
from ..api.models import JudgeInput, JudgementResult, Resource, SkillGap
from ..utils.logger import get_logger
from ..utils.config import get_config


logger = get_logger(__name__)


class JudgeAgent:
    """Autonomous agent that validates resources by EXECUTING code examples."""
    
    SYSTEM_PROMPT = """You are an AUTONOMOUS educational content validator with code execution capabilities.

YOUR MISSION:
Validate learning resources by ACTUALLY TESTING if their code examples work.

AUTONOMOUS TOOLS AVAILABLE:
- web_fetch: Fetch resource content to extract code examples
- code_execution: Execute code examples to verify they work
- bash: Run commands to test installations and setups

YOUR AUTONOMOUS VALIDATION WORKFLOW:

STEP 1: FETCH RESOURCE CONTENT
- Use web_fetch to get the actual content from the resource URL
- Extract code examples, exercises, or tutorials
- Identify the programming language and dependencies

STEP 2: TEST CODE EXAMPLES
- Use code_execution to run example code
- Test if examples execute without errors
- Verify outputs match expected results
- Check if installations/setup instructions work

STEP 3: EVALUATE QUALITY
Based on your testing, evaluate:
- Does the resource actually teach the skill?
- Do code examples work correctly?
- Is the difficulty level appropriate?
- Is the content up-to-date and high-quality?

STEP 4: OUTPUT JUDGEMENT
Return a JSON object:
{
    "resource_id": "string (URL)",
    "is_relevant": boolean,
    "relevance_score": float (0.0-1.0),
    "reasoning": "string (explain what you tested)",
    "recommended": boolean,
    "code_tests_passed": integer,
    "code_tests_failed": integer,
    "technical_quality": "excellent|good|fair|poor"
}

SCORING GUIDELINES:
- 0.9-1.0: Code examples work perfectly, excellent content
- 0.7-0.9: Most examples work, good quality content  
- 0.5-0.7: Some issues but acceptable
- Below 0.5: Broken examples or poor quality

CRITICAL: You MUST use code_execution to test examples. Don't just read - EXECUTE!
"""
    
    def __init__(
        self,
        api_key: str = None,
        relevance_threshold: float = 0.7,
        validate_top_n: int = 5
    ):
        """Initialize Autonomous Judge Agent.
        
        Args:
            api_key: Anthropic API key (optional, will use config if not provided)
            relevance_threshold: Minimum score to consider relevant
            validate_top_n: Number of top resources to validate per skill
        """
        self.config = get_config()
        self.api_key = api_key or self.config.anthropic_api_key
        self.relevance_threshold = relevance_threshold
        self.validate_top_n = validate_top_n
        self.logger = logger
    
    async def validate_resources(
        self,
        skill_gap: SkillGap,
        resources: List[Resource]
    ) -> List[Resource]:
        """Autonomously validate resources by testing code examples.
        
        Args:
            skill_gap: The skill gap to validate resources for
            resources: List of candidate resources
            
        Returns:
            Filtered list of validated resources with test results
        """
        if not resources:
            return []
        
        self.logger.info("=" * 80)
        self.logger.info("⚖️  AUTONOMOUS JUDGE AGENT - VALIDATING WITH CODE EXECUTION")
        self.logger.info("=" * 80)
        self.logger.info(f"\n📥 INPUT:")
        self.logger.info(f"Skill: {skill_gap.skill_name}")
        self.logger.info(f"Required Level: {skill_gap.required_level}")
        self.logger.info(f"Resources to test: {len(resources)} (will execute code from top {min(len(resources), self.validate_top_n)})")
        
        # Validate top N resources with code execution
        resources_to_validate = resources[:self.validate_top_n]
        validated_resources = []
        
        self.logger.info("\n🤖 Launching autonomous validators (will execute code examples)...\n")
        
        for i, resource in enumerate(resources_to_validate, 1):
            try:
                self.logger.info(f"   Testing resource {i}/{len(resources_to_validate)}: {resource.title}")
                self.logger.info(f"   URL: {resource.url}")
                
                # Launch autonomous validation with code execution
                judgement = await self._autonomous_validate(skill_gap, resource)
                
                if judgement:
                    tests_passed = judgement.get("code_tests_passed", 0)
                    tests_failed = judgement.get("code_tests_failed", 0)
                    score = judgement.get("relevance_score", 0.0)
                    quality = judgement.get("technical_quality", "unknown")
                    
                    self.logger.info(f"   Code Tests: {tests_passed} passed, {tests_failed} failed")
                    self.logger.info(f"   Quality: {quality}, Score: {score:.2f}")
                    
                    # Filter based on relevance score
                    if score >= self.relevance_threshold:
                        validated_resources.append(resource)
                        self.logger.info(f"   ✅ PASSED - {judgement.get('reasoning', 'No reason provided')[:100]}...\n")
                    else:
                        self.logger.info(f"   ❌ REJECTED - {judgement.get('reasoning', 'No reason provided')[:100]}...\n")
                else:
                    # If autonomous validation failed, include anyway
                    validated_resources.append(resource)
                    self.logger.info(f"   ⚠️  Validation incomplete, including anyway\n")
                    
            except Exception as e:
                self.logger.error(f"   ❌ Validation error for '{resource.title}': {e}")
                # Include resource anyway if validation fails
                validated_resources.append(resource)
        
        # Add remaining resources without validation
        if len(resources) > self.validate_top_n:
            remaining = len(resources) - self.validate_top_n
            validated_resources.extend(resources[self.validate_top_n:])
            self.logger.info(f"\n   ⏭️  Added {remaining} remaining resources without code testing")
        
        self.logger.info(f"\n📤 AUTONOMOUS VALIDATION COMPLETE:")
        self.logger.info(
            f"Result: {len(validated_resources)}/{len(resources)} resources kept "
            f"for {skill_gap.skill_name}"
        )
        self.logger.info("=" * 80 + "\n")
        
        return validated_resources
    
    async def _autonomous_validate(
        self,
        skill_gap: SkillGap,
        resource: Resource
    ) -> Dict[str, Any]:
        """Launch autonomous agent to validate a resource with code execution.
        
        Args:
            skill_gap: Skill gap context
            resource: Resource to validate
            
        Returns:
            Judgement dictionary with test results
        """
        client = None
        try:
            # Initialize agent client
            client = ClaudeSDKClient()
            await client.connect()
            
            # Construct validation task
            task_prompt = self._construct_validation_task(skill_gap, resource)
            
            # Configure agent with code execution tools
            options = ClaudeAgentOptions(
                system_prompt=self.SYSTEM_PROMPT,
                permission_mode="acceptEdits",  # Allow autonomous code execution
                model=self.config.claude_model
            )
            
            # Send task to agent with options
            await client.send_message(task_prompt, options=options)
            
            # Collect agent's autonomous actions and judgement
            agent_actions = []
            final_judgement = None
            
            async for message in client.receive_messages():
                if message.role == "assistant":
                    agent_actions.append(message)
                    
                    # Look for final JSON judgement
                    for block in message.content:
                        if isinstance(block, TextBlock) and "{" in block.text:
                            try:
                                # Extract JSON
                                text = block.text.strip()
                                if text.startswith("```json"):
                                    text = text[7:]
                                if text.startswith("```"):
                                    text = text[3:]
                                if text.endswith("```"):
                                    text = text[:-3]
                                text = text.strip()
                                
                                # Parse JSON
                                if "{" in text:
                                    # Find JSON object
                                    start = text.find("{")
                                    end = text.rfind("}") + 1
                                    if start >= 0 and end > start:
                                        json_str = text[start:end]
                                        parsed = json.loads(json_str)
                                        if "relevance_score" in parsed:
                                            final_judgement = parsed
                                            break
                            except:
                                continue
                
                # Stop if we have judgement
                if final_judgement:
                    break
            
            # Disconnect
            await client.disconnect()
            
            # Log agent activity
            code_executions = len([a for a in agent_actions if 'execute' in str(a).lower() or 'run' in str(a).lower()])
            self.logger.info(f"   Agent performed: ~{code_executions} code executions")
            
            return final_judgement
            
        except Exception as e:
            self.logger.error(f"   Autonomous validation failed: {e}")
            if client:
                await client.disconnect()
            return None
    
    def _construct_validation_task(
        self,
        skill_gap: SkillGap,
        resource: Resource
    ) -> str:
        """Construct autonomous validation task for the agent.
        
        Args:
            skill_gap: Skill gap context
            resource: Resource to validate
            
        Returns:
            Task prompt for agent
        """
        prompt = f"""AUTONOMOUS VALIDATION TASK: Test Resource with Code Execution

RESOURCE TO VALIDATE:
- Title: {resource.title}
- URL: {resource.url}
- Provider: {resource.provider}
- Type: {resource.resource_type}
- Stated Level: {resource.difficulty_level}

SKILL GAP CONTEXT:
- Skill Needed: {skill_gap.skill_name}
- Required Level: {skill_gap.required_level}
- Priority: {skill_gap.priority}

YOUR AUTONOMOUS MISSION:

1. FETCH THE RESOURCE
   - Use web_fetch to get content from: {resource.url}
   - Extract code examples, tutorials, exercises

2. TEST CODE EXAMPLES
   - Use code_execution to run example code
   - Test at least 2-3 examples if available
   - Verify they execute without errors
   - Check if outputs are correct

3. EVALUATE QUALITY
   Based on your testing:
   - Does it actually teach "{skill_gap.skill_name}"?
   - Do examples work?
   - Is difficulty appropriate for "{skill_gap.required_level}" level?
   - Is content up-to-date?

4. OUTPUT JUDGEMENT JSON
   Return ONLY the judgement JSON (no extra text).

REMEMBER: You MUST use code_execution to test examples. Execute, don't just analyze!

Begin your autonomous validation with code execution now!"""
        
        return prompt
