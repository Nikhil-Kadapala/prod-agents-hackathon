"""Redis client for semantic caching."""

import hashlib
import json
import logging
from typing import Optional
from datetime import timedelta

import redis
from redis.asyncio import Redis as AsyncRedis

from ..api.models import AnalysisResult


logger = logging.getLogger(__name__)


class RedisCache:
    """Redis client for caching skill analysis results."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl_days: int = 7,
        similarity_threshold: float = 0.85
    ):
        """Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            ttl_days: Time-to-live for cached entries in days
            similarity_threshold: Threshold for semantic similarity matching
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.ttl = timedelta(days=ttl_days)
        self.similarity_threshold = similarity_threshold
        
        # Initialize async Redis client
        self.client = AsyncRedis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        
        self.logger = logger
        self.logger.info(f"Initialized Redis cache at {host}:{port}")
    
    def _generate_cache_key(self, resume_text: str, job_description: str) -> str:
        """Generate cache key from input texts.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            
        Returns:
            Cache key string
        """
        # Create hash of combined inputs
        combined = f"{resume_text}|{job_description}"
        hash_obj = hashlib.sha256(combined.encode())
        hash_hex = hash_obj.hexdigest()
        
        return f"skill_analysis:{hash_hex}"
    
    async def get_analysis(
        self,
        resume_text: str,
        job_description: str
    ) -> Optional[AnalysisResult]:
        """Get cached analysis result.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            
        Returns:
            Cached AnalysisResult if found, None otherwise
        """
        cache_key = self._generate_cache_key(resume_text, job_description)
        
        try:
            # Check for exact match
            cached_data = await self.client.get(cache_key)
            
            if cached_data:
                self.logger.info(f"Cache hit for key {cache_key}")
                data = json.loads(cached_data)
                return AnalysisResult(**data)
            
            self.logger.debug(f"Cache miss for key {cache_key}")
            
            # TODO: Implement semantic similarity search using embeddings
            # This would require:
            # 1. Generate embedding for input
            # 2. Search for similar embeddings in Redis
            # 3. Return if similarity > threshold
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving from cache: {e}")
            return None
    
    async def cache_analysis(
        self,
        resume_text: str,
        job_description: str,
        analysis_result: AnalysisResult
    ):
        """Cache analysis result.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            analysis_result: Analysis result to cache
        """
        cache_key = self._generate_cache_key(resume_text, job_description)
        
        try:
            # Serialize result
            data = analysis_result.model_dump_json()
            
            # Store with TTL (convert timedelta to seconds)
            await self.client.setex(
                cache_key,
                int(self.ttl.total_seconds()),
                data
            )
            
            self.logger.info(f"Cached analysis with key {cache_key}")
            
            # TODO: Store embedding for semantic search
            # This would require:
            # 1. Generate embedding for input
            # 2. Store in Redis with vector similarity search support
            
        except Exception as e:
            self.logger.error(f"Error caching analysis: {e}")
    
    async def invalidate(self, resume_text: str, job_description: str):
        """Invalidate cached entry.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
        """
        cache_key = self._generate_cache_key(resume_text, job_description)
        
        try:
            await self.client.delete(cache_key)
            self.logger.info(f"Invalidated cache key {cache_key}")
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {e}")
    
    async def clear_all(self):
        """Clear all cached analyses."""
        try:
            # Find all skill_analysis keys
            keys = []
            async for key in self.client.scan_iter(match="skill_analysis:*"):
                keys.append(key)
            
            if keys:
                await self.client.delete(*keys)
                self.logger.info(f"Cleared {len(keys)} cached entries")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False

