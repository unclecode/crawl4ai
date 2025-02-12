from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *
import asyncio
from pydantic import BaseModel, Field

url = r"https://openai.com/api/pricing/"


class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )


from crawl4ai import AsyncWebCrawler


async def main():
    # Use AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
                # provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY'),
                provider="groq/llama-3.1-70b-versatile",
                api_token=os.getenv("GROQ_API_KEY"),
                schema=OpenAIModelFee.model_json_schema(),
                extraction_type="schema",
                instruction="From the crawled content, extract all mentioned model names along with their "
                "fees for input and output tokens. Make sure not to miss anything in the entire content. "
                "One extracted model JSON format should look like this: "
                '{ "model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens" }',
            ),
        )
        print("Success:", result.success)
        model_fees = json.loads(result.extracted_content)
        print(len(model_fees))

        with open(".data/data.json", "w", encoding="utf-8") as f:
            f.write(result.extracted_content)


asyncio.run(main())
