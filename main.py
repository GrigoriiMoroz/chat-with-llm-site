from fastapi import FastAPI

# Create the FastAPI application instance
# This is the core object that handles all routing and requests
app = FastAPI()

# Define a route using a decorator
# @app.get() means "when someone makes a GET request to this path..."
@app.get("/")
def read_root():
    """
    Root endpoint - the homepage
    Returns a simple JSON message
    """
    return {"message": "Welcome to the LLM Chat API"}

@app.get("/hello")
def hello():
    """
    A test endpoint to verify the server is working
    """
    return {"message": "Hello, World!"}