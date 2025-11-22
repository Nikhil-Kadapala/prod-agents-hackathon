"""NotebookLM client for generating learning content (Phase 3)."""

import logging
from typing import Optional, List

import httpx


logger = logging.getLogger(__name__)


class NotebookLMClient:
    """Client for NotebookLM API to generate learning content."""
    
    def __init__(
        self,
        api_key: str,
        api_endpoint: str = "https://notebooklm.google.com/api/v1",
        enabled: bool = False,
        max_duration_minutes: int = 30,
        timeout: int = 60
    ):
        """Initialize NotebookLM client.
        
        Args:
            api_key: API key for authentication
            api_endpoint: API endpoint URL
            enabled: Whether NotebookLM fallback is enabled
            max_duration_minutes: Maximum duration for generated content
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint.rstrip('/')
        self.enabled = enabled
        self.max_duration_minutes = max_duration_minutes
        self.timeout = timeout
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        self.logger = logger
        
        if enabled:
            self.logger.info("NotebookLM content generation enabled")
        else:
            self.logger.info("NotebookLM content generation disabled")
    
    async def generate_content(
        self,
        skill: str,
        starting_level: str,
        duration_hours: int = 10,
        format: str = "audio",
        sources: Optional[List[str]] = None
    ) -> str:
        """Generate learning content using NotebookLM.
        
        Args:
            skill: Skill name
            starting_level: Starting proficiency level
            duration_hours: Desired content duration
            format: Content format ("audio" or "notes")
            sources: List of source documentation URLs
            
        Returns:
            URL to generated content
            
        Raises:
            Exception: If content generation fails
        """
        if not self.enabled:
            raise ValueError("NotebookLM is not enabled")
        
        self.logger.info(f"Generating NotebookLM content for {skill}")
        
        request_body = {
            "skill": skill,
            "starting_level": starting_level,
            "duration_hours": min(duration_hours, self.max_duration_minutes / 60),
            "format": format,
            "sources": sources or []
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_endpoint}/generate",
                    headers=self.headers,
                    json=request_body
                )
                
                response.raise_for_status()
                data = response.json()
                
                content_url = data.get("content_url")
                if not content_url:
                    raise ValueError("No content URL in response")
                
                self.logger.info(f"Generated NotebookLM content: {content_url}")
                return content_url
                
        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"NotebookLM API error: {e.response.status_code} - {e.response.text}"
            )
            raise Exception(f"NotebookLM generation failed: {e.response.status_code}")
        
        except httpx.TimeoutException:
            self.logger.error("NotebookLM API timeout")
            raise Exception("NotebookLM request timed out")
        
        except Exception as e:
            self.logger.error(f"NotebookLM error: {e}")
            raise
    
    async def get_generation_status(self, generation_id: str) -> dict:
        """Check status of content generation.
        
        Args:
            generation_id: Generation job ID
            
        Returns:
            Status information
        """
        if not self.enabled:
            raise ValueError("NotebookLM is not enabled")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.api_endpoint}/status/{generation_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Failed to get generation status: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check NotebookLM API availability.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.enabled:
            return True
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.api_endpoint}/health",
                    headers=self.headers
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.error(f"NotebookLM health check failed: {e}")
            return False

