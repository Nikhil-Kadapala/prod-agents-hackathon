"""Parallel Search API client for educational resource discovery."""

import os
from typing import List, Dict, Any, Optional

from parallel import Parallel

from ..utils.logger import get_logger


logger = get_logger(__name__)


class ParallelTaskAPI:
    """Client for Parallel Search API for educational resource discovery."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.parallel.ai",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """Initialize Parallel Search API client.
        
        Args:
            api_key: Parallel API key
            endpoint: API base URL (not used with SDK, kept for compatibility)
            timeout: Request timeout in seconds (not used with SDK)
            max_retries: Maximum retry attempts (not used with SDK)
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize Parallel SDK client
        self.client = Parallel(api_key=api_key)
        
        self.logger = logger
        self.logger.info("Initialized Parallel Search API client (using Python SDK)")
    
    async def search_educational_resources(
        self,
        skill: str,
        level: str,
        free_only: bool = True,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for educational resources using Parallel Search API.
        
        Args:
            skill: Skill name (e.g., "Kubernetes", "Python")
            level: Proficiency level (e.g., "beginner", "intermediate")
            free_only: Filter for free resources only
            max_results: Maximum number of results to return
            
        Returns:
            List of educational resource dictionaries
        """
        if not self.api_key:
            self.logger.warning("No Parallel API key provided, using mock resources")
            return self._get_mock_resources(skill, level)
        
        try:
            # Build search objective and queries
            free_filter = " that are free" if free_only else ""
            objective = (
                f"Find the best {skill} {level} learning resources{free_filter} "
                f"including courses, tutorials, documentation, and video guides"
            )
            
            search_queries = [
                f"{skill} tutorial {level}",
                f"learn {skill} {level}",
                f"{skill} course for {level}",
                f"{skill} documentation and guides",
            ]
            
            self.logger.info(f"🔍 Searching for: {skill} ({level})")
            self.logger.info(f"   Objective: {objective}")
            self.logger.info(f"   Queries: {search_queries}")
            
            # Search using Parallel Search API
            results = await self._search_resources(
                objective=objective,
                search_queries=search_queries,
                max_results=max_results
            )
            
            if not results:
                self.logger.warning("No resources found via Search API, using mock resources")
                return self._get_mock_resources(skill, level)
            
            self.logger.info(f"   ✅ Retrieved {len(results)} resources from Search API")
            return results
            
        except Exception as e:
            self.logger.error(f"Search API error: {e}")
            self.logger.warning("Falling back to mock resources")
            return self._get_mock_resources(skill, level)
    
    async def _search_resources(
        self,
        objective: str,
        search_queries: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Execute search via Parallel Search API.
        
        Args:
            objective: Natural language objective
            search_queries: List of search queries
            max_results: Maximum results to return
            
        Returns:
            List of resources with title, url, description
        """
        try:
            # Call Parallel Search API using the SDK
            search = self.client.beta.search(
                objective=objective,
                search_queries=search_queries,
                max_results=max_results,
                max_chars_per_result=5000
            )
            
            # Extract and format results
            search_results = search.results if hasattr(search, 'results') else []
            resources = []
            
            for result in search_results:
                # Skip results without URLs
                if not hasattr(result, 'url') or not result.url:
                    continue
                
                # Extract description from excerpts
                description = self._extract_description(result)
                
                resource = {
                    "title": result.title if hasattr(result, 'title') else "Unknown Resource",
                    "url": result.url,
                    "description": description,
                    "provider": self._extract_provider(result.url),
                    "type": self._infer_type(result.title if hasattr(result, 'title') else ""),
                    "difficulty": "intermediate",  # Default, refined by curator
                    "is_free": True,  # Assume search results are accessible
                    "reasoning": "Search result ranked by relevance",
                    "confidence": 0.85
                }
                resources.append(resource)
            
            self.logger.debug(f"   Converted {len(resources)} search results to resources")
            return resources
                
        except Exception as e:
            self.logger.error(f"Error searching resources: {e}")
            return []
    
    def _extract_description(self, result: Any) -> str:
        """Extract description from search result.
        
        Args:
            result: Search result object
            
        Returns:
            Description string
        """
        # Get first excerpt if available
        if hasattr(result, 'excerpts') and result.excerpts:
            excerpt = result.excerpts[0] if isinstance(result.excerpts, list) else str(result.excerpts)
            # Remove "Last updated:" prefix if present
            if "Last updated" in excerpt:
                lines = excerpt.split("\n")
                excerpt = "\n".join(lines[1:]) if len(lines) > 1 else excerpt
            # Clean up and truncate
            excerpt = excerpt.strip()
            return excerpt[:500]
        
        title = result.title if hasattr(result, 'title') else 'topic'
        return f"Resource about {title}"
    
    def _extract_provider(self, url: str) -> str:
        """Extract provider name from URL.
        
        Args:
            url: Resource URL
            
        Returns:
            Provider name
        """
        if "udemy.com" in url:
            return "Udemy"
        elif "coursera.org" in url:
            return "Coursera"
        elif "youtube.com" in url or "youtu.be" in url:
            return "YouTube"
        elif "freecodecamp.org" in url:
            return "freeCodeCamp"
        elif "github.com" in url:
            return "GitHub"
        elif "stackoverflow.com" in url:
            return "Stack Overflow"
        elif "docs." in url or "/docs" in url or "/documentation" in url:
            return "Documentation"
        elif "medium.com" in url:
            return "Medium"
        elif "dev.to" in url:
            return "Dev.to"
        elif "linkedin.com" in url:
            return "LinkedIn Learning"
        elif "pluralsight.com" in url:
            return "Pluralsight"
        elif "educative.io" in url:
            return "Educative"
        else:
            return "Web"
    
    def _infer_type(self, title: str) -> str:
        """Infer resource type from title.
        
        Args:
            title: Resource title
            
        Returns:
            Resource type (course, tutorial, documentation, video, article)
        """
        title_lower = title.lower()
        if any(word in title_lower for word in ["course", "complete", "master"]):
            return "course"
        elif any(word in title_lower for word in ["tutorial", "guide", "how to", "learn"]):
            return "tutorial"
        elif any(word in title_lower for word in ["doc", "reference", "api"]):
            return "documentation"
        elif any(word in title_lower for word in ["video", "youtube"]):
            return "video"
        else:
            return "article"
    
    def _get_mock_resources(self, skill: str, level: str = "beginner") -> List[Dict[str, Any]]:
        """Generate mock learning resources for demo/fallback.
        
        Args:
            skill: Skill name
            level: Difficulty level
            
        Returns:
            List of mock resource dictionaries
        """
        self.logger.info(f"   🎭 Generating mock resources for {skill}")
        
        # Normalize skill name
        skill_lower = skill.lower()
        
        mock_resources = [
            {
                "title": f"{skill} for Beginners - Complete Guide",
                "url": f"https://www.udemy.com/course/{skill_lower}-beginners",
                "description": f"Comprehensive {skill} course covering fundamentals to advanced concepts",
                "provider": "Udemy",
                "type": "course",
                "difficulty": level,
                "is_free": False,
                "reasoning": "Highly rated comprehensive course",
                "confidence": 0.9
            },
            {
                "title": f"Learn {skill} - Free Interactive Tutorial",
                "url": f"https://www.freecodecamp.org/learn/{skill_lower}",
                "description": f"Free interactive {skill} tutorial with hands-on exercises",
                "provider": "freeCodeCamp",
                "type": "tutorial",
                "difficulty": level,
                "is_free": True,
                "reasoning": "Interactive learning with practical examples",
                "confidence": 0.85
            },
            {
                "title": f"{skill} Tutorial for Beginners",
                "url": f"https://www.youtube.com/results?search_query={skill_lower}+tutorial",
                "description": f"Step-by-step {skill} video tutorial for beginners",
                "provider": "YouTube",
                "type": "video",
                "difficulty": level,
                "is_free": True,
                "reasoning": "Visual learning with practical demonstrations",
                "confidence": 0.8
            },
            {
                "title": f"{skill} Complete Course",
                "url": f"https://www.coursera.org/learn/{skill_lower}",
                "description": f"University-level {skill} course with certificate",
                "provider": "Coursera",
                "type": "course",
                "difficulty": level,
                "is_free": True,
                "reasoning": "Academic quality with structured curriculum",
                "confidence": 0.88
            },
        ]
        
        return mock_resources
