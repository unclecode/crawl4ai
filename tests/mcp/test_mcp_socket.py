# pip install "mcp-sdk[ws]" anyio
import anyio, json
from mcp.client.websocket import websocket_client
from mcp.client.session import ClientSession

async def test_list():
    async with websocket_client("ws://localhost:8020/mcp/ws") as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()

            print("tools      :", [t.name for t in (await s.list_tools()).tools])
            print("resources  :", [r.name for r in (await s.list_resources()).resources])
            print("templates  :", [t.name for t in (await s.list_resource_templates()).resource_templates])


async def test_crawl(s: ClientSession) -> None:
    """Hit the @mcp_tool('crawl') endpoint."""
    res = await s.call_tool(
        "crawl",
        {
            "urls": ["https://example.com"],
            "browser_config": {},
            "crawler_config": {},
        },
    )
    print("crawl →", json.loads(res.content[0].text))


async def test_md(s: ClientSession) -> None:
    """Hit the @mcp_tool('md') endpoint."""
    res = await s.call_tool(
        "md",
        {
            "url": "https://example.com",
            "f": "fit",   # or RAW, BM25, LLM
            "q": None,
            "c": "0",
        },
    )
    result = json.loads(res.content[0].text)
    print("md →", result['markdown'][:100], "...")

async def test_screenshot(s: ClientSession):
    res = await s.call_tool(
        "screenshot",
        {
            "url": "https://example.com",
            "screenshot_wait_for": 1.0,
        },
    )
    png_b64 = json.loads(res.content[0].text)["screenshot"]
    print("screenshot →", png_b64[:60], "… (base64)")


async def test_pdf(s: ClientSession):
    res = await s.call_tool(
        "pdf",
        {
            "url": "https://example.com",
        },
    )
    pdf_b64 = json.loads(res.content[0].text)["pdf"]
    print("pdf →", pdf_b64[:60], "… (base64)")

async def test_execute_js(s: ClientSession):
    # click the “More” link on Hacker News front page and wait 1 s
    res = await s.call_tool(
        "execute_js",
        {
            "url": "https://news.ycombinator.com/news",
            "js_code": [
                "await page.click('a.morelink')",
                "await page.waitForTimeout(1000)",
            ],
        },
    )
    crawl_result = json.loads(res.content[0].text)
    print("execute_js → status", crawl_result["success"], "| html len:", len(crawl_result["html"]))
    
async def test_html(s: ClientSession):
    # click the “More” link on Hacker News front page and wait 1 s
    res = await s.call_tool(
        "html",
        {
            "url": "https://news.ycombinator.com/news",
        },
    )
    crawl_result = json.loads(res.content[0].text)
    print("execute_js → status", crawl_result["success"], "| html len:", len(crawl_result["html"]))    
    
async def test_context(s: ClientSession):
    # click the “More” link on Hacker News front page and wait 1 s
    res = await s.call_tool(
        "ask",
        {
            "query": "I hv a question about Crawl4ai library, how to extract internal links when crawling a page?"
        },
    )
    crawl_result = json.loads(res.content[0].text)
    print("execute_js → status", crawl_result["success"], "| html len:", len(crawl_result["html"]))    


async def main() -> None:
    async with websocket_client("ws://localhost:11235/mcp/ws") as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()                       # handshake
            tools = (await s.list_tools()).tools
            print("tools:", [t.name for t in tools])

            # await test_list()
            await test_crawl(s)
            await test_md(s)
            await test_screenshot(s)
            await test_pdf(s)
            await test_execute_js(s)
            await test_html(s)
            await test_context(s)

anyio.run(main)
