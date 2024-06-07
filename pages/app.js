// JavaScript to manage dynamic form changes and logic
document.getElementById("extraction-strategy-select").addEventListener("change", function () {
    const strategy = this.value;
    const providerModelSelect = document.getElementById("provider-model-select");
    const tokenInput = document.getElementById("token-input");
    const instruction = document.getElementById("instruction");
    const semantic_filter = document.getElementById("semantic_filter");
    const instruction_div = document.getElementById("instruction_div");
    const semantic_filter_div = document.getElementById("semantic_filter_div");
    const llm_settings = document.getElementById("llm_settings");

    if (strategy === "LLMExtractionStrategy") {
        // providerModelSelect.disabled = false;
        // tokenInput.disabled = false;
        // semantic_filter.disabled = true;
        // instruction.disabled = false;
        llm_settings.classList.remove("hidden");
        instruction_div.classList.remove("hidden");
        semantic_filter_div.classList.add("hidden");
    } else if (strategy === "NoExtractionStrategy") {
        semantic_filter_div.classList.add("hidden");
        instruction_div.classList.add("hidden");
        llm_settings.classList.add("hidden");
    } else {
        // providerModelSelect.disabled = true;
        // tokenInput.disabled = true;
        // semantic_filter.disabled = false;
        // instruction.disabled = true;
        llm_settings.classList.add("hidden");
        instruction_div.classList.add("hidden");
        semantic_filter_div.classList.remove("hidden");
    }


});

// Get the selected provider model and token from local storage
const storedProviderModel = localStorage.getItem("provider_model");
const storedToken = localStorage.getItem(storedProviderModel);

if (storedProviderModel) {
    document.getElementById("provider-model-select").value = storedProviderModel;
}

if (storedToken) {
    document.getElementById("token-input").value = storedToken;
}

// Handle provider model dropdown change
document.getElementById("provider-model-select").addEventListener("change", () => {
    const selectedProviderModel = document.getElementById("provider-model-select").value;
    const storedToken = localStorage.getItem(selectedProviderModel);

    if (storedToken) {
        document.getElementById("token-input").value = storedToken;
    } else {
        document.getElementById("token-input").value = "";
    }
});

// Fetch total count from the database
axios
    .get("/total-count")
    .then((response) => {
        document.getElementById("total-count").textContent = response.data.count;
    })
    .catch((error) => console.error(error));

// Handle crawl button click
document.getElementById("crawl-btn").addEventListener("click", () => {
    // validate input to have both URL and API token
    // if selected extraction strategy is LLMExtractionStrategy, then API token is required
    if (document.getElementById("extraction-strategy-select").value === "LLMExtractionStrategy") {
        if (!document.getElementById("url-input").value || !document.getElementById("token-input").value) {
            alert("Please enter both URL(s) and API token.");
            return;
        }
    }

    const selectedProviderModel = document.getElementById("provider-model-select").value;
    const apiToken = document.getElementById("token-input").value;
    const extractBlocks = document.getElementById("extract-blocks-checkbox").checked;
    const bypassCache = document.getElementById("bypass-cache-checkbox").checked;

    // Save the selected provider model and token to local storage
    localStorage.setItem("provider_model", selectedProviderModel);
    localStorage.setItem(selectedProviderModel, apiToken);

    const urlsInput = document.getElementById("url-input").value;
    const urls = urlsInput.split(",").map((url) => url.trim());
    const data = {
        urls: urls,
        include_raw_html: true,
        bypass_cache: bypassCache,
        extract_blocks: extractBlocks,
        word_count_threshold: parseInt(document.getElementById("threshold").value),
        extraction_strategy: document.getElementById("extraction-strategy-select").value,
        extraction_strategy_args: {
            provider: selectedProviderModel,
            api_token: apiToken,
            instruction: document.getElementById("instruction").value,
            semantic_filter: document.getElementById("semantic_filter").value,
        },
        chunking_strategy: document.getElementById("chunking-strategy-select").value,
        chunking_strategy_args: {},
        css_selector: document.getElementById("css-selector").value,
        screenshot: document.getElementById("screenshot-checkbox").checked,
        // instruction: document.getElementById("instruction").value,
        // semantic_filter: document.getElementById("semantic_filter").value,
        verbose: true,
    };

    // import requests

    // data = {
    //   "urls": [
    //     "https://www.nbcnews.com/business"
    //   ],
    //   "word_count_threshold": 10,
    //   "extraction_strategy": "NoExtractionStrategy",
    // }
    
    // response = requests.post("https://crawl4ai.com/crawl", json=data) # OR local host if your run locally 
    // print(response.json())

    // save api token to local storage
    localStorage.setItem("api_token", document.getElementById("token-input").value);

    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("result").style.visibility = "hidden";
    document.getElementById("code_help").style.visibility = "hidden";

    axios
        .post("/crawl", data)
        .then((response) => {
            const result = response.data.results[0];
            const parsedJson = JSON.parse(result.extracted_content);
            document.getElementById("json-result").textContent = JSON.stringify(parsedJson, null, 2);
            document.getElementById("cleaned-html-result").textContent = result.cleaned_html;
            document.getElementById("markdown-result").textContent = result.markdown;
            document.getElementById("media-result").textContent = JSON.stringify( result.media, null, 2);
            if (result.screenshot){
                const imgElement = document.createElement("img");
                // Set the src attribute with the base64 data
                imgElement.src = `data:image/png;base64,${result.screenshot}`;
                document.getElementById("screenshot-result").innerHTML = "";
                document.getElementById("screenshot-result").appendChild(imgElement);
            }
            
            // Update code examples dynamically
            const extractionStrategy = data.extraction_strategy;
            const isLLMExtraction = extractionStrategy === "LLMExtractionStrategy";

            // REMOVE API TOKEN FROM CODE EXAMPLES
            data.extraction_strategy_args.api_token = "your_api_token";

            if (data.extraction_strategy === "NoExtractionStrategy") {
                delete data.extraction_strategy_args;
                delete data.extrac_blocks;
            }

            if (data.chunking_strategy === "RegexChunking") {
                delete data.chunking_strategy_args;
            }

            delete data.verbose;

            if (data.css_selector === "") {
                delete data.css_selector;
            }

            if (!data.bypass_cache) {
                delete data.bypass_cache;
            }

            if (!data.extract_blocks) {
                delete data.extract_blocks;
            }

            if (!data.include_raw_html) {
                delete data.include_raw_html;
            }

            document.getElementById(
                "curl-code"
            ).textContent = `curl -X POST -H "Content-Type: application/json" -d '${JSON.stringify({
                ...data,
                api_token: isLLMExtraction ? "your_api_token" : undefined,
            }, null, 2)}' https://crawl4ai.com/crawl`;

            document.getElementById("python-code").textContent = `import requests\n\ndata = ${JSON.stringify(
                { ...data, api_token: isLLMExtraction ? "your_api_token" : undefined },
                null,
                2
            )}\n\nresponse = requests.post("https://crawl4ai.com/crawl", json=data) # OR local host if your run locally \nprint(response.json())`;

            document.getElementById(
                "nodejs-code"
            ).textContent = `const axios = require('axios');\n\nconst data = ${JSON.stringify(
                { ...data, api_token: isLLMExtraction ? "your_api_token" : undefined },
                null,
                2
            )};\n\naxios.post("https://crawl4ai.com/crawl", data) // OR local host if your run locally \n    .then(response => console.log(response.data))\n    .catch(error => console.error(error));`;

            document.getElementById(
                "library-code"
            ).textContent = `from crawl4ai.web_crawler import WebCrawler\nfrom crawl4ai.extraction_strategy import *\nfrom crawl4ai.chunking_strategy import *\n\ncrawler = WebCrawler()\ncrawler.warmup()\n\nresult = crawler.run(\n    url='${
                urls[0]
            }',\n    word_count_threshold=${data.word_count_threshold},\n    extraction_strategy=${
                isLLMExtraction
                    ? `${extractionStrategy}(provider="${data.provider_model}", api_token="${data.api_token}")`
                    : extractionStrategy + "()"
            },\n    chunking_strategy=${data.chunking_strategy}(),\n    bypass_cache=${
                data.bypass_cache
            },\n    css_selector="${data.css_selector}"\n)\nprint(result)`;

            // Highlight code syntax
            hljs.highlightAll();

            // Select JSON tab by default
            document.querySelector('.tab-btn[data-tab="json"]').click();

            document.getElementById("loading").classList.add("hidden");

            document.getElementById("result").style.visibility = "visible";
            document.getElementById("code_help").style.visibility = "visible";

            // increment the total count
            document.getElementById("total-count").textContent =
                parseInt(document.getElementById("total-count").textContent) + 1;
        })
        .catch((error) => {
            console.error(error);
            document.getElementById("loading").classList.add("hidden");
        });
});

// Handle tab clicks
document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("bg-lime-700", "text-white"));
        btn.classList.add("bg-lime-700", "text-white");
        document.querySelectorAll(".tab-content.code pre").forEach((el) => el.classList.add("hidden"));
        document.getElementById(`${tab}-result`).parentElement.classList.remove("hidden");
    });
});

// Handle code tab clicks
document.querySelectorAll(".code-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll(".code-tab-btn").forEach((b) => b.classList.remove("bg-lime-700", "text-white"));
        btn.classList.add("bg-lime-700", "text-white");
        document.querySelectorAll(".tab-content.result pre").forEach((el) => el.classList.add("hidden"));
        document.getElementById(`${tab}-code`).parentElement.classList.remove("hidden");
    });
});

// Handle copy to clipboard button clicks

async function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        return navigator.clipboard.writeText(text);
    } else {
        return fallbackCopyTextToClipboard(text);
    }
}

function fallbackCopyTextToClipboard(text) {
    return new Promise((resolve, reject) => {
        const textArea = document.createElement("textarea");
        textArea.value = text;

        // Avoid scrolling to bottom
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand("copy");
            if (successful) {
                resolve();
            } else {
                reject();
            }
        } catch (err) {
            reject(err);
        }

        document.body.removeChild(textArea);
    });
}

document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const target = btn.dataset.target;
        const code = document.getElementById(target).textContent;
        //navigator.clipboard.writeText(code).then(() => {
        copyToClipboard(code).then(() => {
            btn.textContent = "Copied!";
            setTimeout(() => {
                btn.textContent = "Copy";
            }, 2000);
        });
    });
});

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const extractionResponse = await fetch("/strategies/extraction");
        const extractionStrategies = await extractionResponse.json();

        const chunkingResponse = await fetch("/strategies/chunking");
        const chunkingStrategies = await chunkingResponse.json();

        renderStrategies("extraction-strategies", extractionStrategies);
        renderStrategies("chunking-strategies", chunkingStrategies);
    } catch (error) {
        console.error("Error fetching strategies:", error);
    }
});

function renderStrategies(containerId, strategies) {
    const container = document.getElementById(containerId);
    container.innerHTML = ""; // Clear any existing content
    strategies = JSON.parse(strategies);
    Object.entries(strategies).forEach(([strategy, description]) => {
        const strategyElement = document.createElement("div");
        strategyElement.classList.add("bg-zinc-800", "p-4", "rounded", "shadow-md", "docs-item");

        const strategyDescription = document.createElement("div");
        strategyDescription.classList.add("text-gray-300", "prose", "prose-sm");
        strategyDescription.innerHTML = marked.parse(description);

        strategyElement.appendChild(strategyDescription);

        container.appendChild(strategyElement);
    });
}
document.querySelectorAll(".sidebar a").forEach((link) => {
    link.addEventListener("click", function (event) {
        event.preventDefault();
        document.querySelectorAll(".content-section").forEach((section) => {
            section.classList.remove("active");
        });
        const target = event.target.getAttribute("data-target");
        document.getElementById(target).classList.add("active");
    });
});
// Highlight code syntax
hljs.highlightAll();
