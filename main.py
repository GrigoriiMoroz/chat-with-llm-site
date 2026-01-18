from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Create the FastAPI application instance
# This is the core object that handles all routing and requests
app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Main page
# После того как я добавил отвечать этим респонсом, появился HTML интерфейс
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