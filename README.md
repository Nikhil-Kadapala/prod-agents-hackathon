# Learning Resource Curator 🎓

> AI-powered personalized learning path generator for skill gap analysis

Built for **Production AI Agents Hackathon** at AWS Builders Loft, 525 Market St, SF

## Overview

A **truly autonomous multi-agent system** that doesn't just think—it **acts**. Powered by Claude Agent SDK, our agents autonomously search the web, validate resources, and execute code to ensure quality.

### 🚀 What Makes This Different

This isn't another API wrapper. Our agents are **autonomous**:

✨ **Autonomous Analyzer** - Searches web in real-time for job market data using `web_search`  
🤖 **Autonomous Curator** - Finds resources with `web_search` and validates URLs with `web_fetch`  
⚡ **Autonomous Judge** - EXECUTES code examples with `code_execution` to verify they work  
🧠 **Self-Learning** - Tracks performance and improves over time  
📊 **Real-Time Data** - Uses live job market insights, not static datasets  
🔄 **Parallel Execution** - Multiple autonomous agents work concurrently  
🌐 **Modern UI** - Real-time progress tracking of autonomous agents

## Autonomous Agent Architecture

```
User Request → FastAPI
  ↓
Orchestrator (Meta-Learning)
  ↓
  ├─→ Autonomous Analyzer Agent
  │   ├─ web_search: "Software Engineer skills 2024"
  │   ├─ web_search: "React job requirements"
  │   └─ Returns: Analysis + Real-Time Market Data
  │
  ├─→ Autonomous Curator Agents (Parallel)
  │   ├─ web_search: "Python tutorial beginner"
  │   ├─ web_fetch: Validate each URL
  │   ├─ web_search: "Docker course free"
  │   └─ Returns: Validated Resource URLs
  │
  └─→ Autonomous Judge Agents (Parallel)
      ├─ web_fetch: Get tutorial content
      ├─ code_execution: Test example 1
      ├─ code_execution: Test example 2
      └─ Returns: Only Resources with Working Code
  ↓
Results + Performance Metrics
```

### Autonomous Agent System

1. **🔍 Analyzer Agent** - Autonomously searches web for real-time job market requirements
   - Tools: `web_search`
   - Actions: Searches current job postings, salary data, skill demand
   - Output: Skill gaps + market insights

2. **📚 Curator Agent** - Autonomously finds and validates learning resources
   - Tools: `web_search`, `web_fetch`
   - Actions: Searches for resources, validates URLs, checks quality
   - Output: List of validated, active resource URLs

3. **⚖️ Judge Agent** - Autonomously tests if resources actually work
   - Tools: `web_fetch`, `code_execution`, `bash`
   - Actions: Fetches content, executes code examples, tests installations
   - Output: Only resources with working, tested examples

4. **🎯 Orchestrator** - Coordinates agents and learns from results
   - Tracks agent performance
   - Adapts workflow based on success metrics
   - Self-improving over time

## Tech Stack

- **Language:** Python 3.14+
- **Agent Framework:** Claude Agent SDK (Python)
- **LLM:** Claude 3.5 Sonnet (Direct Anthropic API)
- **Agent Tools:** `web_search`, `web_fetch`, `code_execution`, `bash`
- **API Framework:** FastAPI (async)
- **Caching:** Redis with semantic search
- **Frontend:** HTML/CSS/JavaScript with real-time updates

## Quick Start

### Prerequisites

- Python 3.14+ (or 3.11+)
- **Anthropic API Key** (with Agent SDK access)
- Docker & Docker Compose (optional, for Redis)
- No AWS account needed! 🎉

### 1. Clone & Install

```bash
git clone <repository-url>
cd prod-agents-hackathon
pip install -r requirements.txt
```

**Note:** Phase 3 dependencies (Skyflow) are commented out by default. The MVP works without them. To enable Skyflow, see [PHASE3_DEPENDENCIES.md](PHASE3_DEPENDENCIES.md).

### 2. Configure Environment

Create `.env` file (or copy from `config/env.template`):

```env
# REQUIRED: Anthropic API Key for Agent SDK
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Redis for caching
REDIS_HOST=localhost
REDIS_PORT=6379

# Application settings
LOG_LEVEL=INFO
```

**Note:** You'll need an Anthropic API key with Agent SDK access. Get one at https://console.anthropic.com/

### 3. Start Services

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run application
make run
```

Visit http://localhost:8000

### Docker Deployment

```bash
# Build and start all services
make docker-build
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Example API Call

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Your resume here...",
    "job_description": "Job description here...",
    "target_job_title": "Senior Full Stack Engineer",
    "filters": {
      "free_only": true,
      "max_duration_hours": 100,
      "resource_types": ["course", "tutorial", "video"]
    }
  }'
```

## Project Structure

```
prod-agents-hackathon/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── analyzer.py      # Skill gap analysis
│   │   ├── curator.py       # Resource curation
│   │   ├── judge.py         # LLM-as-a-Judge
│   │   └── orchestrator.py  # Workflow coordination
│   ├── integrations/        # External service clients
│   │   ├── bedrock_client.py
│   │   ├── redis_cache.py
│   │   ├── parallel_api.py
│   │   ├── skyflow_client.py
│   │   └── notebooklm_client.py
│   ├── api/                 # FastAPI application
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── models.py
│   ├── utils/               # Configuration & logging
│   └── frontend/            # Web UI
├── tests/                   # Test suite
├── config/                  # Configuration files
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Development

### Running Tests

```bash
make test                    # Run all tests
pytest tests/test_analyzer.py -v  # Run specific test
```

### Code Quality

```bash
make format                  # Format code with black
make lint                    # Run linters
```

## Implementation Phases

### ✅ Phase 1: MVP (Completed)
- Analyzer Agent with skill gap identification
- Curator Agent with Parallel API integration
- Basic Orchestrator
- FastAPI endpoints
- Web UI

### ✅ Phase 2: Enhanced Features (Completed)
- Redis semantic caching
- LLM-as-a-Judge validation
- Resource filtering
- Comprehensive testing

### ⏳ Phase 3: Production Ready
- Skyflow PII masking
- NotebookLM content generation fallback
- Advanced error handling
- Monitoring & observability

## Technologies & Integrations

### Core Technologies
- **Claude Agent SDK** - Autonomous agent framework with tool use
- **Claude 3.5 Sonnet** - Advanced reasoning and tool execution
- **FastAPI** - High-performance async API framework
- **Redis** - Semantic caching (optional)

### Autonomous Capabilities
- **Web Search** - Real-time data from the internet
- **Web Fetch** - URL validation and content extraction
- **Code Execution** - Testing code examples in sandboxed environment
- **Bash** - Command execution for installations and tests

## Performance Metrics

- **End-to-end latency:** < 30 seconds
- **Cache hit rate:** > 50% for similar resumes
- **Resource relevance:** > 0.7 score threshold
- **Concurrent requests:** 10+ parallel searches

## Contributing

See [SETUP.md](SETUP.md) for detailed setup instructions and [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) for architecture details.

## License

MIT License - see [LICENSE](LICENSE) file

## Hackathon Details

**Challenge:** Build agents that don't just think, they act ✅

**Goal:** Create autonomous, self-improving AI agents that tap into real-time data sources and take meaningful action without human intervention. ✅

**Our Solution:**
- ✅ **Truly Autonomous** - Agents use tools without human intervention
- ✅ **Real-Time Data** - Web search for current job market insights
- ✅ **Takes Action** - Executes code, validates URLs, tests resources
- ✅ **Self-Improving** - Tracks performance metrics and adapts
- ✅ **Parallel Execution** - Multiple agents work concurrently
- ✅ **Production-Ready** - Robust error handling and fallbacks