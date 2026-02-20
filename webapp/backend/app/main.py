from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
import uvicorn
import os
import sys
from contextlib import asynccontextmanager
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("virtualization_backend")

# Add root directory to sys.path to import virtualization_mcp
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try importing the MCP server
try:
    from virtualization_mcp.server import mcp
    logger.info("✅ Successfully imported virtualization_mcp.server")
except ImportError as e:
    logger.error(f"❌ Failed to import virtualization_mcp: {e}")
    mcp = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Virtualization Backend Starting...")
    if mcp:
        logger.info(f"🔌 MCP Server: {mcp.name}")
    yield
    logger.info("🛑 Virtualization Backend Stopping...")


app = FastAPI(title="Virtualization MCP Backend", lifespan=lifespan)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:10760").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mcp_connected": mcp is not None, "python_path": sys.path}


# LLM Provider Models
class LLMProviderConfig(BaseModel):
    id: str
    name: str
    type: Literal["ollama", "lmstudio", "openai", "anthropic"]
    baseUrl: str
    apiKey: Optional[str] = None
    enabled: bool = False
    defaultModel: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    provider: LLMProviderConfig
    model: str
    messages: List[Message]


class TestResult(BaseModel):
    success: bool
    message: str


# LLM Proxy Endpoints
@app.post("/api/llm/providers/test", response_model=TestResult)
async def test_provider(config: LLMProviderConfig):
    """Test connectivity to an LLM provider."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if config.type == "ollama":
                response = await client.get(f"{config.baseUrl}/api/tags")
                if response.status_code == 200:
                    return TestResult(success=True, message="Connected to Ollama successfully")
                return TestResult(success=False, message=f"Ollama returned status {response.status_code}")
            
            elif config.type == "lmstudio":
                response = await client.get(f"{config.baseUrl}/v1/models")
                if response.status_code == 200:
                    return TestResult(success=True, message="Connected to LM Studio successfully")
                return TestResult(success=False, message=f"LM Studio returned status {response.status_code}")
            
            elif config.type == "openai":
                if not config.apiKey:
                    return TestResult(success=False, message="API key required for OpenAI")
                headers = {"Authorization": f"Bearer {config.apiKey}"}
                response = await client.get("https://api.openai.com/v1/models", headers=headers)
                if response.status_code == 200:
                    return TestResult(success=True, message="Connected to OpenAI successfully")
                return TestResult(success=False, message=f"OpenAI returned status {response.status_code}")
            
            elif config.type == "anthropic":
                if not config.apiKey:
                    return TestResult(success=False, message="API key required for Anthropic")
                return TestResult(success=True, message="Anthropic API key configured (connectivity test skipped)")
            
            return TestResult(success=False, message=f"Unknown provider type: {config.type}")
    
    except httpx.ConnectError as e:
        return TestResult(success=False, message=f"Connection failed: {str(e)}")
    except Exception as e:
        return TestResult(success=False, message=f"Error: {str(e)}")


@app.post("/api/llm/chat")
async def chat(request: ChatRequest):
    """Proxy chat requests to the appropriate LLM provider."""
    provider = request.provider
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if provider.type == "ollama":
                # Ollama chat API
                payload = {
                    "model": request.model,
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                    "stream": False,
                }
                response = await client.post(
                    f"{provider.baseUrl}/api/chat",
                    json=payload
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                data = response.json()
                return {"content": data.get("message", {}).get("content", "")}
            
            elif provider.type == "lmstudio":
                # OpenAI-compatible API for LM Studio
                payload = {
                    "model": request.model,
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                }
                response = await client.post(
                    f"{provider.baseUrl}/v1/chat/completions",
                    json=payload
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                data = response.json()
                return {"content": data.get("choices", [{}])[0].get("message", {}).get("content", "")}
            
            elif provider.type == "openai":
                if not provider.apiKey:
                    raise HTTPException(status_code=400, detail="API key required")
                payload = {
                    "model": request.model,
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                }
                headers = {"Authorization": f"Bearer {provider.apiKey}"}
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                data = response.json()
                return {"content": data.get("choices", [{}])[0].get("message", {}).get("content", "")}
            
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider type: {provider.type}")
    
    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"Cannot connect to provider: {str(e)}")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount MCP Server over HTTP (FastMCP feature)
if mcp:
    @app.get("/mcp/tools")
    async def list_tools():
        return [tool.name for tool in mcp.list_tools()]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10761, reload=True)
