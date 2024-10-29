# Crawl4AI

## Episode 11: Extraction Strategies: JSON CSS, LLM, and Cosine

### Quick Intro
Introduce JSON CSS Extraction Strategy for structured data, LLM Extraction Strategy for intelligent parsing, and Cosine Strategy for clustering similar content. Demo: Use JSON CSS to scrape product details from an e-commerce site.

Here’s a comprehensive outline for the **LLM Extraction Strategy** video, covering key details and example applications.

---

### **10.2 LLM Extraction Strategy**

#### **1. Introduction to LLM Extraction Strategy**
   - The LLM Extraction Strategy leverages language models to interpret and extract structured data from complex web content.
   - Unlike traditional CSS selectors, this strategy uses natural language instructions and schemas to guide the extraction, ideal for unstructured or diverse content.
   - Supports **OpenAI**, **Azure OpenAI**, **HuggingFace**, and **Ollama** models, enabling flexibility with both proprietary and open-source providers.

#### **2. Key Components of LLM Extraction Strategy**
   - **Provider**: Specifies the LLM provider (e.g., OpenAI, HuggingFace, Azure).
   - **API Token**: Required for most providers, except Ollama (local LLM model).
   - **Instruction**: Custom extraction instructions sent to the model, providing flexibility in how the data is structured and extracted.
   - **Schema**: Optional, defines structured fields to organize extracted data into JSON format.
   - **Extraction Type**: Supports `"block"` for simpler text blocks or `"schema"` when a structured output format is required.
   - **Chunking Parameters**: Breaks down large documents, with options to adjust chunk size and overlap rate for more accurate extraction across lengthy texts.

#### **3. Basic Extraction Example: OpenAI Model Pricing**
   - **Goal**: Extract model names and their input and output fees from the OpenAI pricing page.
   - **Schema Definition**:
     - **Model Name**: Text for model identification.
     - **Input Fee**: Token cost for input processing.
     - **Output Fee**: Token cost for output generation.

   - **Schema**:
     ```python
     class OpenAIModelFee(BaseModel):
         model_name: str = Field(..., description="Name of the OpenAI model.")
         input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
         output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")
     ```

   - **Example Code**:
     ```python
     async def extract_openai_pricing():
         async with AsyncWebCrawler() as crawler:
             result = await crawler.arun(
                 url="https://openai.com/api/pricing/",
                 extraction_strategy=LLMExtractionStrategy(
                     provider="openai/gpt-4o",
                     api_token=os.getenv("OPENAI_API_KEY"),
                     schema=OpenAIModelFee.schema(),
                     extraction_type="schema",
                     instruction="Extract model names and fees for input and output tokens from the page."
                 ),
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - The extraction strategy combines a schema and detailed instruction to guide the LLM in capturing structured data.
     - Each model’s name, input fee, and output fee are extracted in a JSON format.

#### **4. Knowledge Graph Extraction Example**
   - **Goal**: Extract entities and their relationships from a document for use in a knowledge graph.
   - **Schema Definition**:
     - **Entities**: Individual items with descriptions (e.g., people, organizations).
     - **Relationships**: Connections between entities, including descriptions and relationship types.

   - **Schema**:
     ```python
     class Entity(BaseModel):
         name: str
         description: str

     class Relationship(BaseModel):
         entity1: Entity
         entity2: Entity
         description: str
         relation_type: str

     class KnowledgeGraph(BaseModel):
         entities: List[Entity]
         relationships: List[Relationship]
     ```

   - **Example Code**:
     ```python
     async def extract_knowledge_graph():
         extraction_strategy = LLMExtractionStrategy(
             provider="azure/gpt-4o-mini",
             api_token=os.getenv("AZURE_API_KEY"),
             schema=KnowledgeGraph.schema(),
             extraction_type="schema",
             instruction="Extract entities and relationships from the content to build a knowledge graph."
         )
         async with AsyncWebCrawler() as crawler:
             result = await crawler.arun(
                 url="https://example.com/some-article",
                 extraction_strategy=extraction_strategy,
                 bypass_cache=True
             )
             print(result.extracted_content)
     ```

   - **Explanation**:
     - In this setup, the LLM extracts entities and their relationships based on the schema and instruction.
     - The schema organizes results into a JSON-based knowledge graph format.

#### **5. Key Settings in LLM Extraction**
   - **Chunking Options**:
     - For long pages, set `chunk_token_threshold` to specify maximum token count per section.
     - Adjust `overlap_rate` to control the overlap between chunks, useful for contextual consistency.
   - **Example**:
     ```python
     extraction_strategy = LLMExtractionStrategy(
         provider="openai/gpt-4",
         api_token=os.getenv("OPENAI_API_KEY"),
         chunk_token_threshold=3000,
         overlap_rate=0.2,  # 20% overlap between chunks
         instruction="Extract key insights and relationships."
     )
     ```
   - This setup ensures that longer texts are divided into manageable chunks with slight overlap, enhancing the quality of extraction.

#### **6. Flexible Provider Options for LLM Extraction**
   - **Using Proprietary Models**: OpenAI, Azure, and HuggingFace provide robust language models, often suited for complex or detailed extractions.
   - **Using Open-Source Models**: Ollama and other open-source models can be deployed locally, suitable for offline or cost-effective extraction.
   - **Example Call**:
     ```python
     await extract_structured_data_using_llm("huggingface/meta-llama/Meta-Llama-3.1-8B-Instruct", os.getenv("HUGGINGFACE_API_KEY"))
     await extract_structured_data_using_llm("openai/gpt-4o", os.getenv("OPENAI_API_KEY"))
     await extract_structured_data_using_llm("ollama/llama3.2")   
     ```

#### **7. Complete Example of LLM Extraction Setup**
   - Code to run both the OpenAI pricing and Knowledge Graph extractions, using various providers:
     ```python
     async def main():
         await extract_openai_pricing()
         await extract_knowledge_graph()
     
     if __name__ == "__main__":
         asyncio.run(main())
     ```

#### **8. Wrap Up & Next Steps**
   - Recap the power of LLM extraction for handling unstructured or complex data extraction tasks.
   - Tease the next video: **10.3 Cosine Similarity Strategy** for clustering similar content based on semantic similarity.

---

This outline explains LLM Extraction in Crawl4AI, with examples showing how to extract structured data using custom schemas and instructions. It demonstrates flexibility with multiple providers, ensuring practical application for different use cases.