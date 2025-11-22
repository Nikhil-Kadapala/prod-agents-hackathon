"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

from .routes import router
from ..utils.config import get_config
from ..utils.logger import setup_logger


# Setup logging
config = get_config()
setup_logger(level=config.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Learning Resource Curator API")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Judge agent: {'enabled' if config.enable_judge else 'disabled'}")
    logger.info(f"Cache: {'enabled' if config.enable_cache else 'disabled'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Learning Resource Curator API")


# Create FastAPI app
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="AI-powered learning resource curator for skill gap analysis",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount static files if they exist
static_dir = Path(__file__).parent.parent / "frontend" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount templates
templates_dir = Path(__file__).parent.parent / "frontend" / "templates"


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI page.
    
    Returns:
        HTML response
    """
    index_file = templates_dir / "index.html"
    
    if index_file.exists():
        with open(index_file, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>Learning Resource Curator</title>
                </head>
                <body>
                    <h1>Learning Resource Curator API</h1>
                    <p>Visit <a href="/docs">/docs</a> for API documentation</p>
                </body>
            </html>
            """
        )


@app.get("/api/v1")
async def api_root():
    """API root endpoint.
    
    Returns:
        API information
    """
    return {
        "name": config.app_name,
        "version": config.app_version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.api_reload,
        log_level=config.log_level.lower()
    )

