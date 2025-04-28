from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
import os
from dotenv import load_dotenv
import logging
from typing import Optional, List, Dict, Any
import json
import pathlib

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log presence of OLLAMA_API_KEY
ollama_api_key = os.getenv("OLLAMA_API_KEY")
if ollama_api_key:
    logger.info("OLLAMA_API_KEY is set")
else:
    logger.info("OLLAMA_API_KEY is not set (not required for local Ollama)")

app = FastAPI(title="Local AI Providers API")

# Add logging middleware to confirm requests pass through
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Allow CORS for all origins temporarily for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY_FILE = pathlib.Path("weather_api_key.json")

def save_api_key(key: str):
    with open(API_KEY_FILE, "w") as f:
        json.dump({"weather_api_key": key}, f)

def load_api_key() -> str:
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, "r") as f:
            data = json.load(f)
            return data.get("weather_api_key", "")
    return ""

@app.get("/api/weather/api-key")
async def get_weather_api_key():
    """Get the stored weather API key."""
    key = load_api_key()
    return {"apiKey": key}

class APIKeyRequest(BaseModel):
    apiKey: str

@app.post("/api/weather/api-key")
async def set_weather_api_key(request: APIKeyRequest):
    """Set and store the weather API key."""
    save_api_key(request.apiKey)
    return {"message": "API key saved successfully"}

@app.get("/api/health/ollama")
async def ollama_health_check():
    """Health check endpoint for Ollama server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PROVIDER_CONFIG['ollama']['api_base']}/api/tags")
            response.raise_for_status()
            return {"status": "healthy", "message": "Ollama server is running"}
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        return {"status": "unhealthy", "message": f"Ollama health check failed: {str(e)}"}

# Configuration for local AI providers
PROVIDER_CONFIG = {
    "ollama": {
        "api_base": os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434"),
        "api_key": os.getenv("OLLAMA_API_KEY", None),
        "chat_endpoint": "/api/chat",
        "generate_endpoint": "/api/generate",
    },
    "lmstudio": {
        "api_base": os.getenv("LMSTUDIO_API_BASE_URL", "http://localhost:1234/v1"),
        "api_key": os.getenv("LMSTUDIO_API_KEY", None),
        "endpoint": "/chat/completions",
    },
    "llamacpp": {
        "api_base": os.getenv("LLAMACPP_API_BASE_URL", "http://localhost:8080"),
        "api_key": os.getenv("LLAMACPP_API_KEY", None),
        "endpoint": "/v1/chat/completions",
    },
    "mock": {
        "api_base": None,
        "api_key": None,
        "endpoint": None,
    },
}


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[int] = None


class GenerateRequest(BaseModel):
    model: str
    messages: List[Message]


@app.get("/api/health/ollama")
async def check_ollama_health() -> Dict[str, str]:
    """Check if Ollama server is running and accessible."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PROVIDER_CONFIG['ollama']['api_base']}/api/tags"
            )
            response.raise_for_status()
            return {"status": "healthy", "message": "Ollama server is running"}
    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        return {"status": "unhealthy", "message": f"Ollama server error: {str(e)}"}


@app.get("/api/providers")
async def get_providers() -> List[Dict[str, str]]:
    """Return available local AI providers."""
    return [
        {"id": "ollama", "name": "Ollama AI"},
        {"id": "lmstudio", "name": "LM Studio"},
        {"id": "llamacpp", "name": "Llama.cpp"},
        {"id": "mock", "name": "Mock AI"},
    ]


@app.get("/api/providers/{provider_id}/models")
async def get_models(provider_id: str) -> List[Dict[str, Any]]:
    """Fetch available models for a specific local provider."""
    if provider_id not in PROVIDER_CONFIG:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider_id == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                headers = (
                    {"Authorization": f"Bearer {PROVIDER_CONFIG['ollama']['api_key']}"}
                    if PROVIDER_CONFIG["ollama"]["api_key"]
                    else {}
                )
                response = await client.get(
                    f"{PROVIDER_CONFIG['ollama']['api_base']}/api/tags", headers=headers
                )
                response.raise_for_status()
                data = response.json()
                models = [
                    {
                        "id": model.get("name", model.get("model")),
                        "name": model.get("name", model.get("model")),
                        "status": "active",
                        "description": model.get("details", {}).get("description", ""),
                    }
                    for model in data.get("models", [])
                ]
                return models
        except Exception as e:
            logger.error(f"Error fetching Ollama models: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error fetching Ollama models: {str(e)}"
            )

    elif provider_id == "lmstudio":
        try:
            async with httpx.AsyncClient() as client:
                headers = (
                    {
                        "Authorization": f"Bearer {PROVIDER_CONFIG['lmstudio']['api_key']}"
                    }
                    if PROVIDER_CONFIG["lmstudio"]["api_key"]
                    else {}
                )
                response = await client.get(
                    f"{PROVIDER_CONFIG['lmstudio']['api_base']}/models", headers=headers
                )
                response.raise_for_status()
                data = response.json()
                models = [
                    {
                        "id": model["id"],
                        "name": model.get("name", model["id"]),
                        "status": "active",
                        "description": "LM Studio local model",
                    }
                    for model in data.get("data", [])
                ]
                return models
        except Exception as e:
            logger.warning(f"LM Studio models endpoint not available: {str(e)}")
            return [
                {
                    "id": "local-model",
                    "name": "Local Model",
                    "status": "active",
                    "description": "Default LM Studio model",
                }
            ]

    elif provider_id == "llamacpp":
        try:
            async with httpx.AsyncClient() as client:
                headers = (
                    {
                        "Authorization": f"Bearer {PROVIDER_CONFIG['llamacpp']['api_key']}"
                    }
                    if PROVIDER_CONFIG["llamacpp"]["api_key"]
                    else {}
                )
                response = await client.get(
                    f"{PROVIDER_CONFIG['llamacpp']['api_base']}/models", headers=headers
                )
                response.raise_for_status()
                data = response.json()
                models = [
                    {
                        "id": model["id"],
                        "name": model.get("name", model["id"]),
                        "status": "active",
                        "description": "Llama.cpp local model",
                    }
                    for model in data.get("models", [])
                ]
                return models
        except Exception as e:
            logger.warning(f"Llama.cpp models endpoint not available: {str(e)}")
            return [
                {
                    "id": "local-model",
                    "name": "Local Model",
                    "status": "active",
                    "description": "Default Llama.cpp model",
                }
            ]

    elif provider_id == "mock":
        return [
            {
                "id": "mock-model-1",
                "name": "Mock Model 1",
                "status": "active",
                "description": "Mock model for testing",
            },
            {
                "id": "mock-model-2",
                "name": "Mock Model 2",
                "status": "active",
                "description": "Mock model for testing",
            },
        ]


@app.post("/api/providers/{provider_id}/generate")
async def generate_response(
    provider_id: str, request: GenerateRequest
) -> Dict[str, Any]:
    """Generate a response from the specified local provider and model."""
    if provider_id not in PROVIDER_CONFIG:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider_id == "ollama":
        try:
            headers = (
                {"Authorization": f"Bearer {PROVIDER_CONFIG['ollama']['api_key']}"}
                if PROVIDER_CONFIG["ollama"]["api_key"]
                else {}
            )
            body = {
                "model": request.model,
                "messages": [m.dict(exclude_none=True) for m in request.messages],
                "stream": False,
            }
            logger.debug(
                f"Sending request to Ollama API {PROVIDER_CONFIG['ollama']['chat_endpoint']}: {body} with headers: {headers}"
            )
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PROVIDER_CONFIG['ollama']['api_base']}{PROVIDER_CONFIG['ollama']['chat_endpoint']}",
                    json=body,
                    headers=headers,
                    timeout=60.0,
                )
                logger.debug(f"Ollama API response status: {response.status_code}")
                logger.debug(f"Ollama API response content: {response.text}")
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Ollama API response JSON: {data}")
                content = data.get("message", {}).get("content", "")
                if not content:
                    logger.warning(
                        "No content in Ollama response, trying /api/generate endpoint"
                    )
                    # Fallback to /api/generate
                    body_generate = {
                        "model": request.model,
                        "prompt": "\n".join(
                            [f"{m['role']}: {m['content']}" for m in body["messages"]]
                        ),
                        "stream": False,
                    }
                    response = await client.post(
                        f"{PROVIDER_CONFIG['ollama']['api_base']}{PROVIDER_CONFIG['ollama']['generate_endpoint']}",
                        json=body_generate,
                        headers=headers,
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data.get("response", "")
                return {
                    "message": {
                        "role": "assistant",
                        "content": content,
                        "timestamp": None,
                    },
                    "usage": data.get("usage", {}),
                }
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error generating Ollama response: {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"HTTP error generating Ollama response: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error(f"Request error generating Ollama response: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Request error generating Ollama response: {str(e)}",
            )
        except Exception as e:
            import traceback

            logger.error(
                f"Unexpected error generating Ollama response: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error generating Ollama response: {str(e)}",
            )

    elif provider_id == "lmstudio":
        try:
            headers = (
                {"Authorization": f"Bearer {PROVIDER_CONFIG['lmstudio']['api_key']}"}
                if PROVIDER_CONFIG["lmstudio"]["api_key"]
                else {}
            )
            body = {
                "model": request.model,
                "messages": [m.dict(exclude_none=True) for m in request.messages],
                "stream": False,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PROVIDER_CONFIG['lmstudio']['api_base']}{PROVIDER_CONFIG['lmstudio']['endpoint']}",
                    json=body,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "message": {
                        "role": "assistant",
                        "content": data["choices"][0]["message"]["content"],
                        "timestamp": None,
                    },
                    "usage": data.get("usage", {}),
                }
        except Exception as e:
            logger.error(f"Error generating LM Studio response: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error generating LM Studio response: {str(e)}"
            )

    elif provider_id == "llamacpp":
        try:
            headers = (
                {"Authorization": f"Bearer {PROVIDER_CONFIG['llamacpp']['api_key']}"}
                if PROVIDER_CONFIG["llamacpp"]["api_key"]
                else {}
            )
            body = {
                "model": request.model,
                "messages": [m.dict(exclude_none=True) for m in request.messages],
                "stream": False,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{PROVIDER_CONFIG['llamacpp']['api_base']}{PROVIDER_CONFIG['llamacpp']['endpoint']}",
                    json=body,
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "message": {
                        "role": "assistant",
                        "content": data["choices"][0]["message"]["content"],
                        "timestamp": None,
                    },
                    "usage": data.get("usage", {}),
                }
        except Exception as e:
            logger.error(f"Error generating Llama.cpp response: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error generating Llama.cpp response: {str(e)}"
            )

    elif provider_id == "mock":
        last_message = request.messages[-1] if request.messages else None
        content = (
            f"Mock response to '{last_message.content}' from model {request.model}"
            if last_message
            else "Mock response"
        )
        return {
            "message": {"role": "assistant", "content": content, "timestamp": None},
            "usage": {},
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
