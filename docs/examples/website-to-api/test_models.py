#!/usr/bin/env python3
"""
Test script for the new model management functionality.
This script demonstrates how to save and use custom model configurations.
"""

import asyncio
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_model_management():
    """Test the model management endpoints."""
    
    print("=== Testing Model Management ===")
    
    # 1. List current models
    print("\n1. Listing current models:")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    
    # 2. Save another model configuration (OpenAI example)
    print("\n2. Saving OpenAI model configuration:")
    openai_config = {
        "model_name": "my-openai",
        "provider": "openai",
        "api_token": "your-openai-api-key-here"
    }
    
    response = requests.post(f"{BASE_URL}/models", json=openai_config)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # 3. List models again to see the new ones
    print("\n3. Listing models after adding new ones:")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # 4. Delete a model configuration
    print("\n4. Deleting a model configuration:")
    response = requests.delete(f"{BASE_URL}/models/my-openai")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # 5. Final list of models
    print("\n5. Final list of models:")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Model Management Test Script")
    print("Make sure the API server is running on http://localhost:8000")
    print("=" * 50)
    
    try:
        test_model_management()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the server is running with: python api_server.py")
    except Exception as e:
        print(f"Error: {e}") 