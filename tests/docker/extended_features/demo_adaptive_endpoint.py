#!/usr/bin/env python3
"""
Demo: How users will call the Adaptive Digest endpoint
This shows practical examples of how developers would use the adaptive crawling
feature to intelligently gather relevant content based on queries.
"""

import asyncio
import time
from typing import Any, Dict, Optional

import aiohttp

# Configuration
API_BASE_URL = "http://localhost:11235"
API_TOKEN = None  # Set if your API requires authentication


class AdaptiveEndpointDemo:
    def __init__(self, base_url: str = API_BASE_URL, token: str = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    async def submit_adaptive_job(
        self, start_url: str, query: str, config: Optional[Dict] = None
    ) -> str:
        """Submit an adaptive crawling job and return task ID"""
        payload = {"start_url": start_url, "query": query}

        if config:
            payload["config"] = config

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/adaptive/digest/job",
                headers=self.headers,
                json=payload,
            ) as response:
                if response.status == 202:  # Accepted
                    result = await response.json()
                    return result["task_id"]
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

    async def check_job_status(self, task_id: str) -> Dict[str, Any]:
        """Check the status of an adaptive crawling job"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/adaptive/digest/job/{task_id}", headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

    async def wait_for_completion(
        self, task_id: str, max_wait: int = 300
    ) -> Dict[str, Any]:
        """Poll job status until completion or timeout"""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = await self.check_job_status(task_id)

            if status["status"] == "COMPLETED":
                return status
            elif status["status"] == "FAILED":
                raise Exception(f"Job failed: {status.get('error', 'Unknown error')}")

            print(
                f"⏳ Job {status['status']}... (elapsed: {int(time.time() - start_time)}s)"
            )
            await asyncio.sleep(3)  # Poll every 3 seconds

        raise Exception(f"Job timed out after {max_wait} seconds")

    async def demo_research_assistant(self):
        """Demo: Research assistant for academic papers"""
        print("🔬 Demo: Academic Research Assistant")
        print("=" * 50)

        try:
            print("🚀 Submitting job: Find research on 'machine learning optimization'")

            task_id = await self.submit_adaptive_job(
                start_url="https://arxiv.org",
                query="machine learning optimization techniques recent papers",
                config={
                    "max_depth": 3,
                    "confidence_threshold": 0.7,
                    "max_pages": 20,
                    "content_filters": ["academic", "research"],
                },
            )

            print(f"📋 Job submitted with ID: {task_id}")

            # Wait for completion
            result = await self.wait_for_completion(task_id)

            print("✅ Research completed!")
            print(f"🎯 Confidence score: {result['result']['confidence']:.2f}")
            print(f"📊 Coverage stats: {result['result']['coverage_stats']}")

            # Show relevant content found
            relevant_content = result["result"]["relevant_content"]
            print(f"\n📚 Found {len(relevant_content)} relevant research papers:")

            for i, content in enumerate(relevant_content[:3], 1):
                title = content.get("title", "Untitled")[:60]
                relevance = content.get("relevance_score", 0)
                print(f"  {i}. {title}... (relevance: {relevance:.2f})")

        except Exception as e:
            print(f"❌ Error: {e}")

    async def demo_market_intelligence(self):
        """Demo: Market intelligence gathering"""
        print("\n💼 Demo: Market Intelligence Gathering")
        print("=" * 50)

        try:
            print("🚀 Submitting job: Analyze competitors in 'sustainable packaging'")

            task_id = await self.submit_adaptive_job(
                start_url="https://packagingeurope.com",
                query="sustainable packaging solutions eco-friendly materials competitors market trends",
                config={
                    "max_depth": 4,
                    "confidence_threshold": 0.6,
                    "max_pages": 30,
                    "content_filters": ["business", "industry"],
                    "follow_external_links": True,
                },
            )

            print(f"📋 Job submitted with ID: {task_id}")

            # Wait for completion
            result = await self.wait_for_completion(task_id)

            print("✅ Market analysis completed!")
            print(f"🎯 Intelligence confidence: {result['result']['confidence']:.2f}")

            # Analyze findings
            relevant_content = result["result"]["relevant_content"]
            print(
                f"\n📈 Market intelligence gathered from {len(relevant_content)} sources:"
            )

            companies = set()
            trends = []

            for content in relevant_content:
                # Extract company mentions (simplified)
                text = content.get("content", "")
                if any(
                    word in text.lower()
                    for word in ["company", "corporation", "inc", "ltd"]
                ):
                    # This would be more sophisticated in real implementation
                    companies.add(content.get("source_url", "Unknown"))

                # Extract trend keywords
                if any(
                    word in text.lower() for word in ["trend", "innovation", "future"]
                ):
                    trends.append(content.get("title", "Trend"))

            print(f"🏢 Companies analyzed: {len(companies)}")
            print(f"📊 Trends identified: {len(trends)}")

        except Exception as e:
            print(f"❌ Error: {e}")

    async def demo_content_curation(self):
        """Demo: Content curation for newsletter"""
        print("\n📰 Demo: Content Curation for Tech Newsletter")
        print("=" * 50)

        try:
            print("🚀 Submitting job: Curate content about 'AI developments this week'")

            task_id = await self.submit_adaptive_job(
                start_url="https://techcrunch.com",
                query="artificial intelligence AI developments news this week recent advances",
                config={
                    "max_depth": 2,
                    "confidence_threshold": 0.8,
                    "max_pages": 25,
                    "content_filters": ["news", "recent"],
                    "date_range": "last_7_days",
                },
            )

            print(f"📋 Job submitted with ID: {task_id}")

            # Wait for completion
            result = await self.wait_for_completion(task_id)

            print("✅ Content curation completed!")
            print(f"🎯 Curation confidence: {result['result']['confidence']:.2f}")

            # Process curated content
            relevant_content = result["result"]["relevant_content"]
            print(f"\n📮 Curated {len(relevant_content)} articles for your newsletter:")

            # Group by category/topic
            categories = {
                "AI Research": [],
                "Industry News": [],
                "Product Launches": [],
                "Other": [],
            }

            for content in relevant_content:
                title = content.get("title", "Untitled")
                if any(
                    word in title.lower() for word in ["research", "study", "paper"]
                ):
                    categories["AI Research"].append(content)
                elif any(
                    word in title.lower() for word in ["company", "startup", "funding"]
                ):
                    categories["Industry News"].append(content)
                elif any(
                    word in title.lower() for word in ["launch", "release", "unveil"]
                ):
                    categories["Product Launches"].append(content)
                else:
                    categories["Other"].append(content)

            for category, articles in categories.items():
                if articles:
                    print(f"\n📂 {category} ({len(articles)} articles):")
                    for article in articles[:2]:  # Show top 2 per category
                        title = article.get("title", "Untitled")[:50]
                        print(f"  • {title}...")

        except Exception as e:
            print(f"❌ Error: {e}")

    async def demo_product_research(self):
        """Demo: Product research and comparison"""
        print("\n🛍️ Demo: Product Research & Comparison")
        print("=" * 50)

        try:
            print("🚀 Submitting job: Research 'best wireless headphones 2024'")

            task_id = await self.submit_adaptive_job(
                start_url="https://www.cnet.com",
                query="best wireless headphones 2024 reviews comparison features price",
                config={
                    "max_depth": 3,
                    "confidence_threshold": 0.75,
                    "max_pages": 20,
                    "content_filters": ["review", "comparison"],
                    "extract_structured_data": True,
                },
            )

            print(f"📋 Job submitted with ID: {task_id}")

            # Wait for completion
            result = await self.wait_for_completion(task_id)

            print("✅ Product research completed!")
            print(f"🎯 Research confidence: {result['result']['confidence']:.2f}")

            # Analyze product data
            relevant_content = result["result"]["relevant_content"]
            print(
                f"\n🎧 Product research summary from {len(relevant_content)} sources:"
            )

            # Extract product mentions (simplified example)
            products = {}
            for content in relevant_content:
                text = content.get("content", "").lower()
                # Look for common headphone brands
                brands = [
                    "sony",
                    "bose",
                    "apple",
                    "sennheiser",
                    "jabra",
                    "audio-technica",
                ]
                for brand in brands:
                    if brand in text:
                        if brand not in products:
                            products[brand] = 0
                        products[brand] += 1

            print("🏷️ Product mentions:")
            for product, mentions in sorted(
                products.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                print(f"  {product.title()}: {mentions} mentions")

        except Exception as e:
            print(f"❌ Error: {e}")

    async def demo_monitoring_pipeline(self):
        """Demo: Set up a monitoring pipeline for ongoing content tracking"""
        print("\n📡 Demo: Content Monitoring Pipeline")
        print("=" * 50)

        monitoring_queries = [
            {
                "name": "Brand Mentions",
                "start_url": "https://news.google.com",
                "query": "YourBrand company news mentions",
                "priority": "high",
            },
            {
                "name": "Industry Trends",
                "start_url": "https://techcrunch.com",
                "query": "SaaS industry trends 2024",
                "priority": "medium",
            },
            {
                "name": "Competitor Activity",
                "start_url": "https://crunchbase.com",
                "query": "competitor funding announcements product launches",
                "priority": "high",
            },
        ]

        print("🚀 Starting monitoring pipeline with 3 queries...")

        jobs = {}

        # Submit all monitoring jobs
        for query_config in monitoring_queries:
            print(f"\n📋 Submitting: {query_config['name']}")

            try:
                task_id = await self.submit_adaptive_job(
                    start_url=query_config["start_url"],
                    query=query_config["query"],
                    config={
                        "max_depth": 2,
                        "confidence_threshold": 0.6,
                        "max_pages": 15,
                    },
                )

                jobs[query_config["name"]] = {
                    "task_id": task_id,
                    "priority": query_config["priority"],
                    "status": "submitted",
                }

                print(f"  ✅ Job ID: {task_id}")

            except Exception as e:
                print(f"  ❌ Failed: {e}")

        # Monitor all jobs
        print(f"\n⏳ Monitoring {len(jobs)} jobs...")

        completed_jobs = {}
        max_wait = 180  # 3 minutes total
        start_time = time.time()

        while jobs and (time.time() - start_time) < max_wait:
            for name, job_info in list(jobs.items()):
                try:
                    status = await self.check_job_status(job_info["task_id"])

                    if status["status"] == "COMPLETED":
                        completed_jobs[name] = status
                        del jobs[name]
                        print(f"  ✅ {name} completed")
                    elif status["status"] == "FAILED":
                        print(f"  ❌ {name} failed: {status.get('error', 'Unknown')}")
                        del jobs[name]

                except Exception as e:
                    print(f"  ⚠️ Error checking {name}: {e}")

            if jobs:  # Still have pending jobs
                await asyncio.sleep(5)

        # Summary
        print("\n📊 Monitoring Pipeline Summary:")
        print(f"  ✅ Completed: {len(completed_jobs)} jobs")
        print(f"  ⏳ Pending: {len(jobs)} jobs")

        for name, result in completed_jobs.items():
            confidence = result["result"]["confidence"]
            content_count = len(result["result"]["relevant_content"])
            print(f"    {name}: {content_count} items (confidence: {confidence:.2f})")


async def main():
    """Run all adaptive endpoint demos"""
    print("🧠 Crawl4AI Adaptive Digest Endpoint - User Demo")
    print("=" * 60)
    print("This demo shows how developers use adaptive crawling")
    print("to intelligently gather relevant content based on queries.\n")

    demo = AdaptiveEndpointDemo()

    try:
        # Run individual demos
        await demo.demo_research_assistant()
        await demo.demo_market_intelligence()
        await demo.demo_content_curation()
        await demo.demo_product_research()

        # Run monitoring pipeline demo
        await demo.demo_monitoring_pipeline()

        print("\n🎉 All demos completed successfully!")
        print("\nReal-world usage patterns:")
        print("1. Submit multiple jobs for parallel processing")
        print("2. Poll job status to track progress")
        print("3. Process results when jobs complete")
        print("4. Use confidence scores to filter quality content")
        print("5. Set up monitoring pipelines for ongoing intelligence")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure the Crawl4AI server is running on localhost:11235")


if __name__ == "__main__":
    asyncio.run(main())
