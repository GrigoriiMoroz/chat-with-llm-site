import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==================== ENVIRONMENT ====================

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
if not HUGGING_FACE_API_KEY:
    raise ValueError("HUGGING_FACE_API_KEY not found in environment variables!")

# Hugging Face API configuration
HF_API_URL = (
    "https://router.huggingface.co/models/"
    "meta-llama/Llama-3.1-8B-Instruct"
)

# ==================== APP SETUP ====================

# Create the FastAPI application instance
app = FastAPI()

# Serve static files
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
    Call the Hugging Face Inference API to get LLM response.

    Args:
        user_message: The user's input message

    Returns:
        The LLM's generated response

    Raises:
        HTTPException: If the API call fails
    """
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": user_message,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9,
            "return_full_text": False,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                HF_API_URL,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Hugging Face API error: {response.text}",
                )

            result = response.json()

            # Hugging Face returns a list with one item
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "").strip()

            return "I couldn't generate a response. Please try again."

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to LLM timed out. Please try again.",
        )
    except Exception as e:
        print(f"Error calling LLM: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request.",
        )


# ==================== ENDPOINTS ====================

@app.get("/")
def read_root():
    """Serve the chat UI"""
    return FileResponse("static/index.html")


@app.get("/hello")
def hello():
    """Test endpoint"""
    return {"message": "Hello, World!"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint — receives user messages and returns LLM responses.
    """
    try:
        llm_response = await call_llm(request.message)
        return ChatResponse(response=llm_response)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        )