from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Create the FastAPI application instance
# This is the core object that handles all routing and requests
app = FastAPI()

# Serve static files
# “When someone requests /static/*, serve files from the static/ folder.”
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==================== DATA MODELS ====================
class ChatRequest(BaseModel):
    """
    Model for incoming chat request
    """
    message: str


class ChatResponse(BaseModel):
    """
    Model for outgoing chat request
    """
    response: str


# ==================== ENDPOINTS ====================

# Main page
@app.get("/")
def read_root():
    """Serve the chat UI"""
    return FileResponse("static/index.html")


@app.get("/hello")
def hello():
    """
    A test endpoint to verify the server is working
    """
    return {"message": "Hello, World!"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Receives user messages and returns bot responses.
    Dummy implementation for testing.
    """

    user_message = request.message

    dummy_response = (
        f"You said: '{user_message}'. "
        "(This is a dummy response - LLM will be connected in Phase 5)"
    )

    return ChatResponse(response=dummy_response)
