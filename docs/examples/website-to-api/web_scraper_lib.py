from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
    JsonCssExtractionStrategy,
    LLMExtractionStrategy
)
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from litellm import completion

class ModelConfig:
    """Configuration for LLM models."""
    
    def __init__(self, provider: str, api_token: str):
        self.provider = provider
        self.api_token = api_token
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "api_token": self.api_token
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        return cls(
            provider=data["provider"],
            api_token=data["api_token"]
        )

class WebScraperAgent:
    """
    A mini library that converts any website into a structured data API.
    
    Features:
    1. Provide a URL and tell AI what data you need in plain English
    2. Generate: Agent reverse-engineers the site and deploys custom scraper
    3. Integrate: Use private API endpoint to get structured data
    4. Support for custom LLM models and API keys
    """
    
    def __init__(self, schemas_dir: str = "schemas", models_dir: str = "models"):
        self.schemas_dir = schemas_dir
        self.models_dir = models_dir
        os.makedirs(self.schemas_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
    
    def _generate_schema_key(self, url: str, query: str) -> str:
        """Generate a unique key for schema caching based on URL and query."""
        content = f"{url}:{query}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def save_model_config(self, model_name: str, provider: str, api_token: str) -> bool:
        """
        Save a model configuration for later use.
        
        Args:
            model_name: User-friendly name for the model
            provider: LLM provider (e.g., 'gemini', 'openai', 'anthropic')
            api_token: API token for the provider
            
        Returns:
            True if saved successfully
        """
        try:
            model_config = ModelConfig(provider, api_token)
            config_path = os.path.join(self.models_dir, f"{model_name}.json")
            
            with open(config_path, "w") as f:
                json.dump(model_config.to_dict(), f, indent=2)
            
            print(f"Model configuration saved: {model_name}")
            return True
        except Exception as e:
            print(f"Failed to save model configuration: {e}")
            return False
    
    def load_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        Load a saved model configuration.
        
        Args:
            model_name: Name of the saved model configuration
            
        Returns:
            ModelConfig object or None if not found
        """
        try:
            config_path = os.path.join(self.models_dir, f"{model_name}.json")
            if not os.path.exists(config_path):
                return None
            
            with open(config_path, "r") as f:
                data = json.load(f)
            
            return ModelConfig.from_dict(data)
        except Exception as e:
            print(f"Failed to load model configuration: {e}")
            return None
    
    def list_saved_models(self) -> List[str]:
        """List all saved model configurations."""
        models = []
        for filename in os.listdir(self.models_dir):
            if filename.endswith('.json'):
                models.append(filename[:-5])  # Remove .json extension
        return models
    
    def delete_model_config(self, model_name: str) -> bool:
        """
        Delete a saved model configuration.
        
        Args:
            model_name: Name of the model configuration to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            config_path = os.path.join(self.models_dir, f"{model_name}.json")
            if os.path.exists(config_path):
                os.remove(config_path)
                print(f"Model configuration deleted: {model_name}")
                return True
            return False
        except Exception as e:
            print(f"Failed to delete model configuration: {e}")
            return False
    
    async def _load_or_generate_schema(self, url: str, query: str, session_id: str = "schema_generator", model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Loads schema from cache if exists, otherwise generates using AI.
        This is the "Generate" step - our agent reverse-engineers the site.
        
        Args:
            url: URL to scrape
            query: Query for data extraction
            session_id: Session identifier
            model_name: Name of saved model configuration to use
        """
        schema_key = self._generate_schema_key(url, query)
        schema_path = os.path.join(self.schemas_dir, f"{schema_key}.json")
        
        if os.path.exists(schema_path):
            print(f"Schema found in cache for {url}")
            with open(schema_path, "r") as f:
                return json.load(f)
        
        print(f"Generating new schema for {url}")
        print(f"Query: {query}")
        query += """
        IMPORTANT:
        GENERATE THE SCHEMA WITH ONLY THE FIELDS MENTIONED IN THE QUERY. MAKE SURE THE NUMBER OF FIELDS IN THE SCHEME MATCH THE NUMBER OF FIELDS IN THE QUERY.
        """
        
        # Step 1: Fetch the page HTML
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    session_id=session_id,
                    simulate_user=True,
                    remove_overlay_elements=True,
                    delay_before_return_html=5,
                )
            )
            html = result.fit_html
        
        # Step 2: Generate schema using AI with custom model if specified
        print("AI is analyzing the page structure...")
        
        # Use custom model configuration if provided
        if model_name:
            model_config = self.load_model_config(model_name)
            if model_config:
                llm_config = LLMConfig(
                    provider=model_config.provider,
                    api_token=model_config.api_token
                )
                print(f"Using custom model: {model_name}")
            else:
                raise ValueError(f"Model configuration '{model_name}' not found. Please add it from the Models page.")
        else:
            # Require a model to be specified
            raise ValueError("No model specified. Please select a model from the dropdown or add one from the Models page.")
        
        schema = JsonCssExtractionStrategy.generate_schema(
            html=html,
            llm_config=llm_config,
            query=query
        )
        
        # Step 3: Cache the generated schema
        print(f"Schema generated and cached: {json.dumps(schema, indent=2)}")
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)
        
        return schema
    
    def _generate_llm_schema(self, query: str, llm_config: LLMConfig) -> Dict[str, Any]:
        """
        Generate a schema for a given query using a custom LLM model.
        
        Args:
            query: Plain English description of what data to extract
            model_config: Model configuration to use
        """
        # ask the model to generate a schema for the given query in the form of a json.
        prompt = f"""
        IDENTIFY THE FIELDS FOR EXTRACTION MENTIONED IN THE QUERY and GENERATE A JSON SCHEMA FOR THE FIELDS.
        eg.
        {{
            "name": "str",  
            "age": "str",
            "email": "str",
            "product_name": "str",
            "product_price": "str",
            "product_description": "str",
            "product_image": "str",
            "product_url": "str",
            "product_rating": "str",
            "product_reviews": "str",
        }}
        Here is the query:
        {query}
        IMPORTANT:
        THE RESULT SHOULD BE A JSON OBJECT.
        MAKE SURE THE NUMBER OF FIELDS IN THE RESULT MATCH THE NUMBER OF FIELDS IN THE QUERY.
        THE RESULT SHOULD BE A JSON OBJECT.
        """
        response = completion(
            model=llm_config.provider,
            messages=[{"role": "user", "content": prompt}],
            api_key=llm_config.api_token,
            result_type="json"
        )

        return response.json()["choices"][0]["message"]["content"]
    async def scrape_data_with_llm(self, url: str, query: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape structured data from any website using a custom LLM model.
        
        Args:
            url: The website URL to scrape
            query: Plain English description of what data to extract
            model_name: Name of saved model configuration to use
        """

        if model_name:
            model_config = self.load_model_config(model_name)
            if model_config:
                llm_config = LLMConfig(
                    provider=model_config.provider,
                    api_token=model_config.api_token
                )
                print(f"Using custom model: {model_name}")
            else:
                raise ValueError(f"Model configuration '{model_name}' not found. Please add it from the Models page.")
        else:
            # Require a model to be specified
            raise ValueError("No model specified. Please select a model from the dropdown or add one from the Models page.")

        query += """\n  
        IMPORTANT:
        THE RESULT SHOULD BE A JSON OBJECT WITH THE ONLY THE FIELDS MENTIONED IN THE QUERY.
        MAKE SURE THE NUMBER OF FIELDS IN THE RESULT MATCH THE NUMBER OF FIELDS IN THE QUERY.
        THE RESULT SHOULD BE A JSON OBJECT.
        """

        schema = self._generate_llm_schema(query, llm_config)

        print(f"Schema: {schema}")

        llm_extraction_strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            instruction=query,
            result_type="json",
            schema=schema
        )

        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    simulate_user=True,
                    extraction_strategy=llm_extraction_strategy,
                )
            )
        extracted_data = result.extracted_content
        if isinstance(extracted_data, str):
                try:
                    extracted_data = json.loads(extracted_data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, keep it as string
                    pass
            
        return {
                "url": url,
                "query": query,
                "extracted_data": extracted_data,
                "timestamp": result.timestamp if hasattr(result, 'timestamp') else None
            }
        
    async def scrape_data(self, url: str, query: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to scrape structured data from any website.
        
        Args:
            url: The website URL to scrape
            query: Plain English description of what data to extract
            model_name: Name of saved model configuration to use
            
        Returns:
            Structured data extracted from the website
        """
        # Step 1: Generate or load schema (reverse-engineer the site)
        schema = await self._load_or_generate_schema(url=url, query=query, model_name=model_name)
        
        # Step 2: Deploy custom high-speed scraper
        print(f"Deploying custom scraper for {url}")
        browser_config = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            run_config = CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema=schema),
            )
            result = await crawler.arun(url=url, config=run_config)
            
            # Step 3: Return structured data
            # Parse extracted_content if it's a JSON string
            extracted_data = result.extracted_content
            if isinstance(extracted_data, str):
                try:
                    extracted_data = json.loads(extracted_data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, keep it as string
                    pass
            
            return {
                "url": url,
                "query": query,
                "extracted_data": extracted_data,
                "schema_used": schema,
                "timestamp": result.timestamp if hasattr(result, 'timestamp') else None
            }
    
    async def get_cached_schemas(self) -> Dict[str, str]:
        """Get list of cached schemas."""
        schemas = {}
        for filename in os.listdir(self.schemas_dir):
            if filename.endswith('.json'):
                schema_key = filename[:-5]  # Remove .json extension
                schemas[schema_key] = filename
        return schemas
    
    def clear_cache(self):
        """Clear all cached schemas."""
        import shutil
        if os.path.exists(self.schemas_dir):
            shutil.rmtree(self.schemas_dir)
        os.makedirs(self.schemas_dir, exist_ok=True)
        print("Schema cache cleared")

# Convenience function for simple usage
async def scrape_website(url: str, query: str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to scrape any website with plain English instructions.
    
    Args:
        url: Website URL
        query: Plain English description of what data to extract
        model_name: Name of saved model configuration to use
        
    Returns:
        Extracted structured data
    """
    agent = WebScraperAgent()
    return await agent.scrape_data(url, query, model_name)

async def scrape_website_with_llm(url: str, query: str, model_name: Optional[str] = None):
    """
    Scrape structured data from any website using a custom LLM model.
    
    Args:
        url: The website URL to scrape
        query: Plain English description of what data to extract
        model_name: Name of saved model configuration to use
    """
    agent = WebScraperAgent()
    return await agent.scrape_data_with_llm(url, query, model_name)