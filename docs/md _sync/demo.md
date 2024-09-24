# Interactive Demo for Crowler
<div id="demo">
    <form id="crawlForm" class="terminal-form">
        <fieldset>
            <legend>Enter URL and Options</legend>
            <div class="form-group">
                <label for="url">Enter URL:</label>
                <input type="text" id="url" name="url" required>
            </div>
            <div class="form-group">
                <label for="screenshot">Get Screenshot:</label>
                <input type="checkbox" id="screenshot" name="screenshot">
            </div>
            <div class="form-group">
                <button class="btn btn-default" type="submit">Submit</button>
            </div>

        </fieldset>
    </form>

    <div id="loading" class="loading-message">
        <div class="terminal-alert terminal-alert-primary">Loading... Please wait.</div>
    </div>

    <section id="response" class="response-section">
        <h2>Response</h2>
        <div class="tabs">
            <ul class="tab-list">
                <li class="tab-item" onclick="showTab('markdown')">Markdown</li>
                <li class="tab-item" onclick="showTab('cleanedHtml')">Cleaned HTML</li>
                <li class="tab-item" onclick="showTab('media')">Media</li>
                <li class="tab-item" onclick="showTab('extractedContent')">Extracted Content</li>
                <li class="tab-item" onclick="showTab('screenshot')">Screenshot</li>
                <li class="tab-item" onclick="showTab('pythonCode')">Python Code</li>
            </ul>
            <div class="tab-content" id="tab-markdown">
                <header>
                    <div>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="copyToClipboard('markdownContent')">Copy</button>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="downloadContent('markdownContent', 'markdown.md')">Download</button>
                    </div>
                </header>
                <pre><code id="markdownContent" class="language-markdown hljs"></code></pre>
            </div>

            <div class="tab-content" id="tab-cleanedHtml" style="display: none;">
                <header >
                    <div>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="copyToClipboard('cleanedHtmlContent')">Copy</button>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="downloadContent('cleanedHtmlContent', 'cleaned.html')">Download</button>
                    </div>
                </header>
                <pre><code id="cleanedHtmlContent" class="language-html hljs"></code></pre>
            </div>

            <div class="tab-content" id="tab-media" style="display: none;">
                <header >
                    <div>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="copyToClipboard('mediaContent')">Copy</button>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="downloadContent('mediaContent', 'media.json')">Download</button>
                    </div>
                </header>
                <pre><code id="mediaContent" class="language-json hljs"></code></pre>
            </div>

            <div class="tab-content" id="tab-extractedContent" style="display: none;">
                <header >
                    <div>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="copyToClipboard('extractedContentContent')">Copy</button>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="downloadContent('extractedContentContent', 'extracted_content.json')">Download</button>
                    </div>
                </header>
                <pre><code id="extractedContentContent" class="language-json hljs"></code></pre>
            </div>

            <div class="tab-content" id="tab-screenshot" style="display: none;">
                <header >
                    <div>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="downloadImage('screenshotContent', 'screenshot.png')">Download</button>
                    </div>
                </header>
                <pre><img id="screenshotContent" /></pre>
            </div>

            <div class="tab-content" id="tab-pythonCode" style="display: none;">
                <header >
                    <div>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="copyToClipboard('pythonCode')">Copy</button>
                        <button class="btn btn-default btn-ghost btn-sm" onclick="downloadContent('pythonCode', 'example.py')">Download</button>
                    </div>
                </header>
                <pre><code id="pythonCode" class="language-python hljs"></code></pre>
            </div>
        </div>
    </section>

    <div id="error" class="error-message" style="display: none; margin-top:1em;">
        <div class="terminal-alert terminal-alert-error"></div>
    </div>

    <script>
        function showTab(tabId) {
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.style.display = 'none');
            document.getElementById(`tab-${tabId}`).style.display = 'block';
        }

        function redo(codeBlock, codeText){
            codeBlock.classList.remove('hljs');
            codeBlock.removeAttribute('data-highlighted');

            // Set new code and re-highlight
            codeBlock.textContent = codeText;
            hljs.highlightBlock(codeBlock);
        }

        function copyToClipboard(elementId) {
            const content = document.getElementById(elementId).textContent;
            navigator.clipboard.writeText(content).then(() => {
                alert('Copied to clipboard');
            });
        }

        function downloadContent(elementId, filename) {
            const content = document.getElementById(elementId).textContent;
            const blob = new Blob([content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        }

        function downloadImage(elementId, filename) {
            const content = document.getElementById(elementId).src;
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = content;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        document.getElementById('crawlForm').addEventListener('submit', function(event) {
            event.preventDefault();
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';

            const url = document.getElementById('url').value;
            const screenshot = document.getElementById('screenshot').checked;
            const data = {
                urls: [url],
                bypass_cache: false,
                word_count_threshold: 5,
                screenshot: screenshot
            };

            fetch('/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 429) {
                        return response.json().then(err => { 
                            throw Object.assign(new Error('Rate limit exceeded'), { status: 429, details: err });
                        });
                    }
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                data = data.results[0]; // Only one URL is requested
                document.getElementById('loading').style.display = 'none';
                document.getElementById('response').style.display = 'block';
                redo(document.getElementById('markdownContent'), data.markdown);
                redo(document.getElementById('cleanedHtmlContent'), data.cleaned_html);
                redo(document.getElementById('mediaContent'), JSON.stringify(data.media, null, 2));
                redo(document.getElementById('extractedContentContent'), data.extracted_content);
                if (screenshot) {
                    document.getElementById('screenshotContent').src = `data:image/png;base64,${data.screenshot}`;
                }
                const pythonCode = `
from crawl4ai.web_crawler import WebCrawler

crawler = WebCrawler()
crawler.warmup()

result = crawler.run(
    url='${url}',
    screenshot=${screenshot}
)
print(result)
                `;
                redo(document.getElementById('pythonCode'), pythonCode);
                document.getElementById('error').style.display = 'none';
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                let errorMessage = 'An unexpected error occurred. Please try again later.';
                
                if (error.status === 429) {
                    const details = error.details;
                    if (details.retry_after) {
                        errorMessage = `Rate limit exceeded. Please wait ${parseFloat(details.retry_after).toFixed(1)} seconds before trying again.`;
                    } else if (details.reset_at) {
                        const resetTime = new Date(details.reset_at);
                        const waitTime = Math.ceil((resetTime - new Date()) / 1000);
                        errorMessage = `Rate limit exceeded. Please try again after ${waitTime} seconds.`;
                    } else {
                        errorMessage = `Rate limit exceeded. Please try again later.`;
                    }
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                document.querySelector('#error .terminal-alert').textContent = errorMessage;
            });
        });
    </script>
</div>