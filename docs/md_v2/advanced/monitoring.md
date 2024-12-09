# Monitoring with OpenTelemetry

Crawl4AI integrates with [OpenLIT](https://github.com/openlit/openlit) OpenTelemetry auto-instrumentation to perform real-time monitoring of your web crawling agents.

Monitoring can enhance your Crawl4AI usage with auto-generated traces and metrics for

1. **Performance Optimization:** Automatically trace and analyze latency to resolve performance bottlenecks efficiently.  
2. **Request Insights:** Capture essential request metadata automatically for in-depth analysis.  
3. **Comprehensive Monitoring in LLM Usage:** Obtain complete execution traces with task sequence, LLM costs, and latency when Crawl4AI is used along with LLMs and AI agents.

## Installation and Setup

We start by installing `openlit` SDK. Use the following commands to install them:

```bash
pip install openlit
```

### Step 1: Deploy OpenLIT Stack

1. Git Clone OpenLIT Repository

   Open your command line or terminal and run:

   ```shell
   git clone git@github.com:openlit/openlit.git
   ```

2. Self-host using Docker

   Deploy and run OpenLIT with the following command:

   ```shell
   docker compose up -d
   ```

> For instructions on installing in Kubernetes using Helm, refer to the [Kubernetes Helm installation guide](https://docs.openlit.io/latest/installation#kubernetes).

### Instrument the application with OpenLIT

Once we have imported our required modules, All you have to do is add the below two lines in your appliation code

```python
import openlit

openlit.init()
```

For an example setup, let's set up our WebCrawler client and OpenTelemetry automatic-instrumentation with OpenLIT.

```python
import asyncio
from crawl4ai import AsyncWebCrawler
import openlit

openlit.init()

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://www.nbcnews.com/business")

        # Print the extracted content
        print(result.markdown)

# Run the async main function
asyncio.run(main())
```

### Native OpenTelemetry Support

> 💡 Info: If the `otlp_endpoint` or `OTEL_EXPORTER_OTLP_ENDPOINT` is not provided, the OpenLIT SDK will output traces directly to your console, which is recommended during the development phase.
OpenLIT can send complete execution traces and metrics directly from your application to any OpenTelemetry endpoint. Configure the telemetry data destination as follows:

| Purpose                                   | Parameter/Environment Variable                   | For Sending to OpenLIT         |
|-------------------------------------------|--------------------------------------------------|--------------------------------|
| Send data to an HTTP OTLP endpoint        | `otlp_endpoint` or `OTEL_EXPORTER_OTLP_ENDPOINT` | `"http://127.0.0.1:4318"`      |
| Authenticate telemetry backends           | `otlp_headers` or `OTEL_EXPORTER_OTLP_HEADERS`   | Not required by default        |

### Step 4: Visualize and Optimize!
With the Observability data now being collected and sent to OpenLIT, the next step is to visualize and analyze this data to get insights into your AI application's performance, behavior, and identify areas of improvement.

Just head over to OpenLIT at `127.0.0.1:3000` on your browser to start exploring. You can login using the default credentials
  - **Email**: `user@openlit.io`
  - **Password**: `openlituser`

If you're sending metrics and traces to other observability tools, take a look at OpenLIT's [Connections Guide](https://docs.openlit.io/latest/connections/intro) to start using a pre-built dashboard they have created for these tools.
