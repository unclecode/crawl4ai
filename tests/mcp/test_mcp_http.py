from mcp.client.streamable_http import streamablehttp_client
from mcp.client.session import ClientSession

async def main():
    async with streamablehttp_client("http://0.0.0.0:11234/mcp/http") as (r,s,_):
        async with ClientSession(r,s) as sess:
            print(await sess.list_tools())      
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())