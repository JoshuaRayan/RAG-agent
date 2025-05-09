from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio
import os
from pathlib import Path
import logging

from agent.agent import OllamaAgent
from config import API_HOST, API_PORT

# Create FastAPI app
app = FastAPI(title="Federal Registry Search API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Initialize agent
agent = OllamaAgent()

# Set up logger
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None

class SearchResponse(BaseModel):
    response: str

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    await agent.init()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await agent.close()

@app.get("/")
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search the Federal Registry using natural language.
    
    Args:
        request: Search request containing the query and optional chat_id
        
    Returns:
        Search response containing the agent's response
    """
    try:
        response = await agent.process_message(request.query, request.chat_id)
        
        # Handle different response formats
        if isinstance(response, dict):
            if 'message' in response and 'content' in response['message']:
                return SearchResponse(response=response['message']['content'])
            elif 'content' in response:
                return SearchResponse(response=response['content'])
        
        # If response is a string, return it directly
        if isinstance(response, str):
            return SearchResponse(response=response)
            
        # If we can't parse the response, return it as a string
        return SearchResponse(response=str(response))
        
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

def start():
    """Start the FastAPI server."""
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )

if __name__ == "__main__":
    start()
