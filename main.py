import os
import logging
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==================== SETUP ====================

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
if not HUGGING_FACE_API_KEY:
    raise ValueError("HUGGING_FACE_API_KEY not found in environment variables!")

# Model to use for chat - using meta-llama (original choice)
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
# Router endpoint - OpenAI-compatible chat completions API
API_URL = "https://router.huggingface.co/v1/chat/completions"

# ==================== APP SETUP ====================

# Create the FastAPI application instance
app = FastAPI()

# Serve static files (HTML, CSS, JavaScript)
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# ==================== DATA MODELS ====================

class ChatRequest(BaseModel):
    """Model for incoming chat request"""
    message: str


class ChatResponse(BaseModel):
    """Model for outgoing chat response"""
    response: str


# ==================== LLM FUNCTION ====================

async def call_llm(user_message: str) -> str:
    """
    Generate a response using Hugging Face Inference API directly.

    Args:
        user_message: The user's input message

    Returns:
        The LLM's generated response

    Raises:
        ValueError: For user-facing errors (shown in chat)
    """
    logger.info(f"Generating response for: {user_message[:50]}...")

    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json",
    }

    # OpenAI-compatible format
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Calling Hugging Face API at {API_URL}")
            response = await client.post(API_URL, headers=headers, json=payload)

            logger.info(f"Response status: {response.status_code}")

            if response.status_code == 503:
                logger.warning("Model is loading")
                raise ValueError(
                    "⏳ The model is loading (can take 20-60 seconds on first use). "
                    "Please try again in a moment!"
                )

            if response.status_code == 403:
                logger.error("Access forbidden")
                raise ValueError(
                    f"Access denied. You may need to accept the model license at "
                    f"https://huggingface.co/{MODEL_NAME}"
                )

            if response.status_code == 401:
                logger.error("Authentication failed")
                raise ValueError("Invalid or missing Hugging Face API token")

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"API error: Status={response.status_code}, Body={error_text}")
                logger.error(f"Request URL: {API_URL}")
                logger.error(f"Request headers: {headers}")
                logger.error(f"Request payload: {payload}")
                raise ValueError(f"API error ({response.status_code}): {error_text}")

            result = response.json()
            logger.info(f"Raw response: {result}")

            # Parse OpenAI-compatible response format
            # Response structure: {"choices": [{"message": {"content": "..."}}]}
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
            else:
                # Fallback for unexpected format
                logger.warning(f"Unexpected response format: {result}")
                generated_text = str(result)

            logger.info("Response generated successfully")
            return generated_text.strip()

    except httpx.TimeoutException:
        logger.error("Request timeout")
        raise ValueError("Request timed out. The model may be loading. Please try again.")

    except ValueError:
        # Re-raise ValueError (our custom errors)
        raise

    except Exception as e:
        import traceback
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"An unexpected error occurred: {str(e)}")


# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    """Serve the chat UI"""
    return FileResponse("static/index.html")


@app.get("/hello")
def hello():
    """Test endpoint to verify server is running"""
    return {"message": "Hello, World!"}


@app.get("/test-api")
async def test_api():
    """
    Test endpoint to verify Hugging Face connection works.
    Visit: http://localhost:8000/test-api

    This is helpful for debugging - it tells you exactly what's wrong!
    """
    try:
        result = await call_llm("Say hello!")
        return {"success": True, "response": result}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint — receives user messages and returns LLM responses.
    """
    try:
        llm_response = await call_llm(request.message)
        return ChatResponse(response=llm_response)

    except ValueError as e:
        # Return user-friendly error message in the chat
        return ChatResponse(response=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        return ChatResponse(response="An unexpected error occurred. Please try again.")
