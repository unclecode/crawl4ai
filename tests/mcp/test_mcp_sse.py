from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def main():
    async with sse_client("http://127.0.0.1:8020/mcp") as (r, w):
        async with ClientSession(r, w) as sess:
            print(await sess.list_tools())      # now works
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
