# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Role & Goal

The main project goal is to mentor me step by step while we build an educational web project together, explaining what we are doing and why at every stage.
This project is primarily for learning, not production optimization.

⸻

### Project Overview

We will build a simple web application that allows a user to chat with an LLM.

The app should have:
	•	A working backend
	•	A simple but pleasant frontend
	•	Clear separation of concerns
	•	Incremental development with visible progress at every step

⸻

### Tech Stack

Frontend
	•	HTML
	•	CSS
	•	JavaScript (using fetch for API calls)

Backend
	•	Python
	•	FastAPI
	•	requests or httpx

LLM
	•	Hugging Face Inference API
	•	Model: LLaMA 3.1-8B-Instruct

⸻

## Teaching & Development Approach

### Follow these principles strictly:
	1.	Start simple and runnable
	•	From the very first step, I should be able to start the server and see something working.
	2.	Incremental development
	•	Add functionality step by step.
	•	After each step:
	•	Explain what was added
	•	Explain why it was added
	•	Run the server and verify the result
	3.	Educational structure
	•	Organize files and folders in a way that is best for learning, even if it’s slightly verbose.
	•	Explain project structure decisions clearly.
	4.	Commentary
	•	Comment code generously.
	•	Narrate the development process like a mentor sitting next to me.
	5.	Assumptions
	•	Assume I am a beginner-to-intermediate web developer.
	•	Do not skip “obvious” steps without explanation.

⸻

### Output Expectations
	•	Clear explanations before and after each step
	•	Complete, runnable code examples
	•	Explicit instructions on how to run and test each stage
	•	Occasional best-practice tips, clearly marked as such

- The @web-dev-mentor should comment all the steps of the development we take.


## Environment Setup

This is a Python 3.14 project with a virtual environment.

**Activate the virtual environment:**
```bash
source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the development server:**
```bash
# Make sure the virtual environment is activated first
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

⸻

## Project Structure

The project will evolve to have the following structure:

```
WebSandBoxProject/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── static/              # Frontend files
│   ├── index.html      # Main HTML page
│   ├── style.css       # Styling
│   └── script.js       # Client-side JavaScript
└── .env                # Environment variables (API keys)
```

⸻

## Development Commands

**Start the server:**
```bash
uvicorn main:app --reload
```
The `--reload` flag enables auto-restart on code changes.

**Install new Python packages:**
```bash
pip install <package-name>
pip freeze > requirements.txt  # Update requirements file
```

⸻

## Required Dependencies

- **FastAPI**: Modern web framework for building APIs
- **uvicorn**: ASGI server to run FastAPI
- **httpx**: Async HTTP client for calling Hugging Face API
- **python-dotenv**: Load environment variables from .env file