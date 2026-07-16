from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional, Union, List
import uvicorn
import asyncio
import os
import json
from datetime import datetime
from web_scraper_lib import WebScraperAgent, scrape_website

app = FastAPI(
    title="Web Scraper API",
    description="Convert any website into a structured data API. Provide a URL and tell AI what data you need in plain English.",
    version="1.0.0"
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount assets directory
if os.path.exists("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Initialize the scraper agent
scraper_agent = WebScraperAgent()

# Create directory for saved API requests
os.makedirs("saved_requests", exist_ok=True)

class ScrapeRequest(BaseModel):
    url: HttpUrl
    query: str
    model_name: Optional[str] = None

class ModelConfigRequest(BaseModel):
    model_name: str
    provider: str
    api_token: str

class ScrapeResponse(BaseModel):
    success: bool
    url: str
    query: str
    extracted_data: Union[Dict[str, Any], list]
    schema_used: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None

class SavedApiRequest(BaseModel):
    id: str
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    timestamp: str
    response: Optional[Dict[str, Any]] = None

def save_api_request(endpoint: str, method: str, headers: Dict[str, str], body: Dict[str, Any], response: Optional[Dict[str, Any]] = None) -> str:
    """Save an API request to a JSON file."""
    
    # Check for duplicate requests (same URL and query)
    if endpoint in ["/scrape", "/scrape-with-llm"] and "url" in body and "query" in body:
        existing_requests = get_saved_requests()
        for existing_request in existing_requests:
            if (existing_request.endpoint == endpoint and 
                existing_request.body.get("url") == body["url"] and 
                existing_request.body.get("query") == body["query"]):
                print(f"Duplicate request found for URL: {body['url']} and query: {body['query']}")
                return existing_request.id  # Return existing request ID instead of creating new one
    
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    
    saved_request = SavedApiRequest(
        id=request_id,
        endpoint=endpoint,
        method=method,
        headers=headers,
        body=body,
        timestamp=datetime.now().isoformat(),
        response=response
    )
    
    file_path = os.path.join("saved_requests", f"{request_id}.json")
    with open(file_path, "w") as f:
        json.dump(saved_request.dict(), f, indent=2)
    
    return request_id

def get_saved_requests() -> List[SavedApiRequest]:
    """Get all saved API requests."""
    requests = []
    if os.path.exists("saved_requests"):
        for filename in os.listdir("saved_requests"):
            if filename.endswith('.json'):
                file_path = os.path.join("saved_requests", filename)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        requests.append(SavedApiRequest(**data))
                except Exception as e:
                    print(f"Error loading saved request {filename}: {e}")
    
    # Sort by timestamp (newest first)
    requests.sort(key=lambda x: x.timestamp, reverse=True)
    return requests

@app.get("/")
async def root():
    """Serve the frontend interface."""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    else:
        return {
            "message": "Web Scraper API",
            "description": "Convert any website into structured data with AI",
            "endpoints": {
                "/scrape": "POST - Scrape data from a website",
                "/schemas": "GET - List cached schemas",
                "/clear-cache": "POST - Clear schema cache",
                "/models": "GET - List saved model configurations",
                "/models": "POST - Save a new model configuration",
                "/models/{model_name}": "DELETE - Delete a model configuration",
                "/saved-requests": "GET - List saved API requests"
            }
        }

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_website_endpoint(request: ScrapeRequest):
    """
    Scrape structured data from any website.
    
    This endpoint:
    1. Takes a URL and plain English query
    2. Generates a custom scraper using AI
    3. Returns structured data
    """
    try:
        # Save the API request
        headers = {"Content-Type": "application/json"}
        body = {
            "url": str(request.url),
            "query": request.query,
            "model_name": request.model_name
        }
        
        result = await scraper_agent.scrape_data(
            url=str(request.url),
            query=request.query,
            model_name=request.model_name
        )
        
        response_data = ScrapeResponse(
            success=True,
            url=result["url"],
            query=result["query"],
            extracted_data=result["extracted_data"],
            schema_used=result["schema_used"],
            timestamp=result["timestamp"]
        )
        
        # Save the request with response
        save_api_request(
            endpoint="/scrape",
            method="POST",
            headers=headers,
            body=body,
            response=response_data.dict()
        )
        
        return response_data
    
    except Exception as e:
        # Save the failed request
        headers = {"Content-Type": "application/json"}
        body = {
            "url": str(request.url),
            "query": request.query,
            "model_name": request.model_name
        }
        
        save_api_request(
            endpoint="/scrape",
            method="POST",
            headers=headers,
            body=body,
            response={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.post("/scrape-with-llm", response_model=ScrapeResponse)
async def scrape_website_endpoint_with_llm(request: ScrapeRequest):
    """
    Scrape structured data from any website using a custom LLM model.
    """
    try:
        # Save the API request
        headers = {"Content-Type": "application/json"}
        body = {
            "url": str(request.url),
            "query": request.query,
            "model_name": request.model_name
        }
        
        result = await scraper_agent.scrape_data_with_llm(
            url=str(request.url),
            query=request.query,
            model_name=request.model_name
        )
        
        response_data = ScrapeResponse(
            success=True,
            url=result["url"],
            query=result["query"],
            extracted_data=result["extracted_data"],
            timestamp=result["timestamp"]
        )
        
        # Save the request with response
        save_api_request(
            endpoint="/scrape-with-llm",
            method="POST",
            headers=headers,
            body=body,
            response=response_data.dict()
        )
        
        return response_data
    
    except Exception as e:
        # Save the failed request
        headers = {"Content-Type": "application/json"}
        body = {
            "url": str(request.url),
            "query": request.query,
            "model_name": request.model_name
        }
        
        save_api_request(
            endpoint="/scrape-with-llm",
            method="POST",
            headers=headers,
            body=body,
            response={"error": str(e)}
        )
        
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/saved-requests")
async def list_saved_requests():
    """List all saved API requests."""
    try:
        requests = get_saved_requests()
        return {
            "success": True,
            "requests": [req.dict() for req in requests],
            "count": len(requests)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list saved requests: {str(e)}")

@app.delete("/saved-requests/{request_id}")
async def delete_saved_request(request_id: str):
    """Delete a saved API request."""
    try:
        file_path = os.path.join("saved_requests", f"{request_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return {
                "success": True,
                "message": f"Saved request '{request_id}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Saved request '{request_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete saved request: {str(e)}")

@app.get("/schemas")
async def list_cached_schemas():
    """List all cached schemas."""
    try:
        schemas = await scraper_agent.get_cached_schemas()
        return {
            "success": True,
            "cached_schemas": schemas,
            "count": len(schemas)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schemas: {str(e)}")

@app.post("/clear-cache")
async def clear_schema_cache():
    """Clear all cached schemas."""
    try:
        scraper_agent.clear_cache()
        return {
            "success": True,
            "message": "Schema cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/models")
async def list_models():
    """List all saved model configurations."""
    try:
        models = scraper_agent.list_saved_models()
        return {
            "success": True,
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@app.post("/models")
async def save_model_config(request: ModelConfigRequest):
    """Save a new model configuration."""
    try:
        success = scraper_agent.save_model_config(
            model_name=request.model_name,
            provider=request.provider,
            api_token=request.api_token
        )
        
        if success:
            return {
                "success": True,
                "message": f"Model configuration '{request.model_name}' saved successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save model configuration")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save model: {str(e)}")

@app.delete("/models/{model_name}")
async def delete_model_config(model_name: str):
    """Delete a model configuration."""
    try:
        success = scraper_agent.delete_model_config(model_name)
        
        if success:
            return {
                "success": True,
                "message": f"Model configuration '{model_name}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Model configuration '{model_name}' not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "web-scraper-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)