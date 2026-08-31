// ==== File: docs/ask_ai/ask-ai.js (Marked, Streaming, History) ====

document.addEventListener("DOMContentLoaded", () => {
    console.log("AI Assistant JS V2 Loaded");

    // --- DOM Element Selectors ---
    const historyList = document.getElementById("history-list");
    const newChatButton = document.getElementById("new-chat-button");
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendButton = document.getElementById("send-button");
    const citationsList = document.getElementById("citations-list");

    // --- Constants ---
    const CHAT_INDEX_KEY = "aiAssistantChatIndex_v1";
    const CHAT_PREFIX = "aiAssistantChat_v1_";

    // --- State ---
    let currentChatId = null;
    let conversationHistory = []; // Holds message objects { sender: 'user'/'ai', text: '...' }
    let isThinking = false;
    let streamInterval = null; // To control the streaming interval

    // --- Event Listeners ---
    sendButton.addEventListener("click", handleSendMessage);
    chatInput.addEventListener("keydown", handleInputKeydown);
    newChatButton.addEventListener("click", handleNewChat);
    chatInput.addEventListener("input", autoGrowTextarea);

    // --- Initialization ---
    loadChatHistoryIndex(); // Load history list on startup
    const initialQuery = checkForInitialQuery(window.parent.location); // Check for query param
    if (!initialQuery) {
        loadInitialChat(); // Load normally if no query
    }

    // --- Core Functions ---

    function handleSendMessage() {
        const userMessageText = chatInput.value.trim();
        if (!userMessageText || isThinking) return;

        setThinking(true); // Start thinking state

        // Add user message to state and UI
        const userMessage = { sender: "user", text: userMessageText };
        conversationHistory.push(userMessage);
        addMessageToChat(userMessage, false); // Add user message without parsing markdown

        chatInput.value = "";
        autoGrowTextarea(); // Reset textarea height

        // Prepare for AI response (create empty div)
        const aiMessageDiv = addMessageToChat({ sender: "ai", text: "" }, true); // Add empty div with thinking indicator

        // TODO: Generate fingerprint/JWT here

        // TODO: Send `conversationHistory` + JWT to backend API
        // Replace placeholder below with actual API call
        // The backend should ideally return a stream of text tokens

        // --- Placeholder Streaming Simulation ---
        const simulatedFullResponse = `Okay, Here’s a minimal Python script that creates an AsyncWebCrawler, fetches a webpage, and prints the first 300 characters of its Markdown output:

\`\`\`python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:300])  # Print first 300 chars

if __name__ == "__main__":
    asyncio.run(main())
\`\`\`

A code snippet: \`crawler.run()\`. Check the [quickstart](/core/quickstart).`;

        // Simulate receiving the response stream
        streamSimulatedResponse(aiMessageDiv, simulatedFullResponse);

        // // Simulate receiving citations *after* stream starts (or with first chunk)
        // setTimeout(() => {
        //     addCitations([
        //         { title: "Simulated Doc 1", url: "#sim1" },
        //         { title: "Another Concept", url: "#sim2" },
        //     ]);
        // }, 500); // Citations appear shortly after thinking starts
    }

    function handleInputKeydown(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSendMessage();
        }
    }

    function addMessageToChat(message, addThinkingIndicator = false) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${message.sender}-message`);

        // Parse markdown and set HTML
        messageDiv.innerHTML = message.text ? marked.parse(message.text) : "";

        if (message.sender === "ai") {
            // Apply Syntax Highlighting AFTER setting innerHTML
            messageDiv.querySelectorAll("pre code:not(.hljs)").forEach((block) => {
                if (typeof hljs !== "undefined") {
                    // Check if already highlighted to prevent double-highlighting issues
                    if (!block.classList.contains("hljs")) {
                        hljs.highlightElement(block);
                    }
                } else {
                    console.warn("highlight.js (hljs) not found for syntax highlighting.");
                }
            });

            // Add thinking indicator if needed (and not already present)
            if (addThinkingIndicator && !message.text && !messageDiv.querySelector(".thinking-indicator-cursor")) {
                const thinkingDiv = document.createElement("div");
                thinkingDiv.className = "thinking-indicator-cursor";
                messageDiv.appendChild(thinkingDiv);
            }
        } else {
            // User messages remain plain text
            // messageDiv.textContent = message.text;
        }

        // wrap each pre in a div.terminal
        messageDiv.querySelectorAll("pre").forEach((block) => {
            const wrapper = document.createElement("div");
            wrapper.className = "terminal";
            block.parentNode.insertBefore(wrapper, block);
            wrapper.appendChild(block);
        });

        chatMessages.appendChild(messageDiv);
        // Scroll only if user is near the bottom? (More advanced)
        // Simple scroll for now:
        scrollToBottom();
        return messageDiv; // Return the created element
    }

    function streamSimulatedResponse(messageDiv, fullText) {
        const thinkingIndicator = messageDiv.querySelector(".thinking-indicator-cursor");
        if (thinkingIndicator) thinkingIndicator.remove();

        const tokens = fullText.split(/(\s+)/);
        let currentText = "";
        let tokenIndex = 0;
        // Clear previous interval just in case
        if (streamInterval) clearInterval(streamInterval);

        streamInterval = setInterval(() => {
            const cursorSpan = '<span class="thinking-indicator-cursor"></span>'; // Cursor for streaming
            if (tokenIndex < tokens.length) {
                currentText += tokens[tokenIndex];
                // Render intermediate markdown + cursor
                messageDiv.innerHTML = marked.parse(currentText + cursorSpan);
                // Re-highlight code blocks on each stream update - might be slightly inefficient
                // but ensures partial code blocks look okay. Highlight only final on completion.
                // messageDiv.querySelectorAll('pre code:not(.hljs)').forEach((block) => {
                //     hljs.highlightElement(block);
                // });
                scrollToBottom(); // Keep scrolling as content streams
                tokenIndex++;
            } else {
                // Streaming finished
                clearInterval(streamInterval);
                streamInterval = null;

                // Final render without cursor
                messageDiv.innerHTML = marked.parse(currentText);

                // === Final Syntax Highlighting ===
                messageDiv.querySelectorAll("pre code:not(.hljs)").forEach((block) => {
                    if (typeof hljs !== "undefined" && !block.classList.contains("hljs")) {
                        hljs.highlightElement(block);
                    }
                });

                // === Extract Citations ===
                const citations = extractMarkdownLinks(currentText);

                // Wrap each pre in a div.terminal
                messageDiv.querySelectorAll("pre").forEach((block) => {
                    const wrapper = document.createElement("div");
                    wrapper.className = "terminal";
                    block.parentNode.insertBefore(wrapper, block);
                    wrapper.appendChild(block);
                });

                const aiMessage = { sender: "ai", text: currentText, citations: citations };
                conversationHistory.push(aiMessage);
                updateCitationsDisplay();
                saveCurrentChat();
                setThinking(false);
            }
        }, 50); // Adjust speed
    }

    // === NEW Function to Extract Links ===
    function extractMarkdownLinks(markdownText) {
        const regex = /\[([^\]]+)\]\(([^)]+)\)/g; // [text](url)
        const citations = [];
        let match;
        while ((match = regex.exec(markdownText)) !== null) {
            // Avoid adding self-links from within the citations list if AI includes them
            if (!match[2].startsWith("#citation-")) {
                citations.push({
                    title: match[1].trim(),
                    url: match[2].trim(),
                });
            }
        }
        // Optional: Deduplicate links based on URL
        const uniqueCitations = citations.filter(
            (citation, index, self) => index === self.findIndex((c) => c.url === citation.url)
        );
        return uniqueCitations;
    }

    // === REVISED Function to Display Citations ===
    function updateCitationsDisplay() {
        let lastCitations = null;
        // Find the most recent AI message with citations
        for (let i = conversationHistory.length - 1; i >= 0; i--) {
            if (
                conversationHistory[i].sender === "ai" &&
                conversationHistory[i].citations &&
                conversationHistory[i].citations.length > 0
            ) {
                lastCitations = conversationHistory[i].citations;
                break; // Found the latest citations
            }
        }

        citationsList.innerHTML = ""; // Clear previous
        if (!lastCitations) {
            citationsList.innerHTML = '<li class="no-citations">No citations available.</li>';
            return;
        }

        lastCitations.forEach((citation, index) => {
            const li = document.createElement("li");
            const a = document.createElement("a");
            // Generate a unique ID for potential internal linking if needed
            // a.id = `citation-${index}`;
            a.href = citation.url || "#";
            a.textContent = citation.title;
            a.target = "_top"; // Open in main window
            li.appendChild(a);
            citationsList.appendChild(li);
        });
    }

    function addCitations(citations) {
        citationsList.innerHTML = ""; // Clear
        if (!citations || citations.length === 0) {
            citationsList.innerHTML = '<li class="no-citations">No citations available.</li>';
            return;
        }
        citations.forEach((citation) => {
            const li = document.createElement("li");
            const a = document.createElement("a");
            a.href = citation.url || "#";
            a.textContent = citation.title;
            a.target = "_top"; // Open in main window
            li.appendChild(a);
            citationsList.appendChild(li);
        });
    }

    function setThinking(thinking) {
        isThinking = thinking;
        sendButton.disabled = thinking;
        chatInput.disabled = thinking;
        chatInput.placeholder = thinking ? "AI is responding..." : "Ask about Crawl4AI...";
        // Stop any existing stream if we start thinking again (e.g., rapid resend)
        if (thinking && streamInterval) {
            clearInterval(streamInterval);
            streamInterval = null;
        }
    }

    function autoGrowTextarea() {
        chatInput.style.height = "auto";
        chatInput.style.height = `${chatInput.scrollHeight}px`;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // --- Query Parameter Handling ---
    function checkForInitialQuery(locationToCheck) {
        // <-- Receive location object
        if (!locationToCheck) {
            console.warn("Ask AI: Could not access parent window location.");
            return false;
        }
        const urlParams = new URLSearchParams(locationToCheck.search); // <-- Use passed location's search string
        const encodedQuery = urlParams.get("qq"); // <-- Use 'qq'

        if (encodedQuery) {
            console.log("Initial query found (qq):", encodedQuery);
            try {
                const decodedText = decodeURIComponent(escape(atob(encodedQuery)));
                console.log("Decoded query:", decodedText);

                // Start new chat immediately
                handleNewChat(true);

                // Delay setting input and sending message slightly
                setTimeout(() => {
                    chatInput.value = decodedText;
                    autoGrowTextarea();
                    handleSendMessage();

                    // Clean the PARENT window's URL
                    try {
                        const cleanUrl = locationToCheck.pathname;
                        // Use parent's history object
                        window.parent.history.replaceState({}, window.parent.document.title, cleanUrl);
                    } catch (e) {
                        console.warn("Ask AI: Could not clean parent URL using replaceState.", e);
                        // This might fail due to cross-origin restrictions if served differently,
                        // but should work fine with mkdocs serve on the same origin.
                    }
                }, 100);

                return true; // Query processed
            } catch (e) {
                console.error("Error decoding initial query (qq):", e);
                // Clean the PARENT window's URL even on error
                try {
                    const cleanUrl = locationToCheck.pathname;
                    window.parent.history.replaceState({}, window.parent.document.title, cleanUrl);
                } catch (cleanError) {
                    console.warn("Ask AI: Could not clean parent URL after decode error.", cleanError);
                }
                return false;
            }
        }
        return false; // No 'qq' query found
    }

    // --- History Management ---

    function handleNewChat(isFromQuery = false) {
        if (isThinking) return; // Don't allow new chat while responding

        // Only save if NOT triggered immediately by a query parameter load
        if (!isFromQuery) {
            saveCurrentChat();
        }

        currentChatId = `chat_${Date.now()}`;
        conversationHistory = []; // Clear message history state
        chatMessages.innerHTML = ""; // Start with clean slate for query
        if (!isFromQuery) {
            // Show welcome only if manually started
            // chatMessages.innerHTML =
            //     '<div class="message ai-message welcome-message">Started a new chat! Ask me anything about Crawl4AI.</div>';
            chatMessages.innerHTML =
                '<div class="message ai-message welcome-message">We will launch this feature very soon.</div>';
        }
        addCitations([]); // Clear citations
        updateCitationsDisplay(); // Clear UI

        // Add to index and save
        let index = loadChatIndex();
        // Generate a generic title initially, update later
        const newTitle = isFromQuery ? "Chat from Selection" : `Chat ${new Date().toLocaleString()}`;
        // index.unshift({ id: currentChatId, title: `Chat ${new Date().toLocaleString()}` }); // Add to start
        index.unshift({ id: currentChatId, title: newTitle });
        saveChatIndex(index);

        renderHistoryList(index); // Update UI
        setActiveHistoryItem(currentChatId);
        saveCurrentChat(); // Save the empty new chat state
    }

    function loadChat(chatId) {
        if (isThinking || chatId === currentChatId) return;

        // Check if chat data actually exists before proceeding
        const storedChat = localStorage.getItem(CHAT_PREFIX + chatId);
        if (storedChat === null) {
            console.warn(`Attempted to load non-existent chat: ${chatId}. Removing from index.`);
            deleteChatData(chatId); // Clean up index
            loadChatHistoryIndex(); // Reload history list
            loadInitialChat(); // Load next available chat
            return;
        }

        console.log(`Loading chat: ${chatId}`);
        saveCurrentChat(); // Save current before switching

        try {
            conversationHistory = JSON.parse(storedChat);
            currentChatId = chatId;
            renderChatMessages(conversationHistory);
            updateCitationsDisplay();
            setActiveHistoryItem(chatId);
        } catch (e) {
            console.error("Error loading chat:", chatId, e);
            alert("Failed to load chat data.");
            conversationHistory = [];
            renderChatMessages(conversationHistory);
            updateCitationsDisplay();
        }
    }

    function saveCurrentChat() {
        if (currentChatId && conversationHistory.length > 0) {
            try {
                localStorage.setItem(CHAT_PREFIX + currentChatId, JSON.stringify(conversationHistory));
                console.log(`Chat ${currentChatId} saved.`);

                // Update title in index (e.g., use first user message)
                let index = loadChatIndex();
                const currentItem = index.find((item) => item.id === currentChatId);
                if (
                    currentItem &&
                    conversationHistory[0]?.sender === "user" &&
                    !currentItem.title.startsWith("Chat about:")
                ) {
                    currentItem.title = `Chat about: ${conversationHistory[0].text.substring(0, 30)}...`;
                    saveChatIndex(index);
                    // Re-render history list if title changed - small optimization needed here maybe
                    renderHistoryList(index);
                    setActiveHistoryItem(currentChatId); // Re-set active after re-render
                }
            } catch (e) {
                console.error("Error saving chat:", currentChatId, e);
                // Handle potential storage full errors
                if (e.name === "QuotaExceededError") {
                    alert("Local storage is full. Cannot save chat history.");
                    // Consider implementing history pruning logic here
                }
            }
        } else if (currentChatId) {
            // Save empty state for newly created chats if needed, or remove?
            localStorage.setItem(CHAT_PREFIX + currentChatId, JSON.stringify([]));
        }
    }

    function loadChatIndex() {
        try {
            const storedIndex = localStorage.getItem(CHAT_INDEX_KEY);
            return storedIndex ? JSON.parse(storedIndex) : [];
        } catch (e) {
            console.error("Error loading chat index:", e);
            return []; // Return empty array on error
        }
    }

    function saveChatIndex(indexArray) {
        try {
            localStorage.setItem(CHAT_INDEX_KEY, JSON.stringify(indexArray));
        } catch (e) {
            console.error("Error saving chat index:", e);
        }
    }

    function renderHistoryList(indexArray) {
        historyList.innerHTML = ""; // Clear existing
        if (!indexArray || indexArray.length === 0) {
            historyList.innerHTML = '<li class="no-history">No past chats found.</li>';
            return;
        }
        indexArray.forEach((item) => {
            const li = document.createElement("li");
            li.dataset.chatId = item.id; // Add ID to li for easier selection

            const a = document.createElement("a");
            a.href = "#";
            a.dataset.chatId = item.id;
            a.textContent = item.title || `Chat ${item.id.split("_")[1] || item.id}`;
            a.title = a.textContent; // Tooltip for potentially long titles
            a.addEventListener("click", (e) => {
                e.preventDefault();
                loadChat(item.id);
            });

            // === Add Delete Button ===
            const deleteBtn = document.createElement("button");
            deleteBtn.className = "delete-chat-btn";
            deleteBtn.innerHTML = "✕"; // Trash can emoji/icon (or use text/SVG/FontAwesome)
            deleteBtn.title = "Delete Chat";
            deleteBtn.dataset.chatId = item.id; // Store ID on button too
            deleteBtn.addEventListener("click", handleDeleteChat);

            li.appendChild(a);
            li.appendChild(deleteBtn); // Append button to the list item
            historyList.appendChild(li);
        });
    }

    function renderChatMessages(messages) {
        chatMessages.innerHTML = ""; // Clear existing messages
        messages.forEach((message) => {
            // Ensure highlighting is applied when loading from history
            addMessageToChat(message, false);
        });
        if (messages.length === 0) {
            // chatMessages.innerHTML =
            //     '<div class="message ai-message welcome-message">Chat history loaded. Ask a question!</div>';
            chatMessages.innerHTML =
                '<div class="message ai-message welcome-message">We will launch this feature very soon.</div>';
        }
        // Scroll to bottom after loading messages
        scrollToBottom();
    }

    function setActiveHistoryItem(chatId) {
        document.querySelectorAll("#history-list li").forEach((li) => li.classList.remove("active"));
        // Select the LI element directly now
        const activeLi = document.querySelector(`#history-list li[data-chat-id="${chatId}"]`);
        if (activeLi) {
            activeLi.classList.add("active");
        }
    }

    function loadInitialChat() {
        const index = loadChatIndex();
        if (index.length > 0) {
            loadChat(index[0].id);
        } else {
            // Check if handleNewChat wasn't already called by query handler
            if (!currentChatId) {
                handleNewChat();
            }
        }
    }

    function loadChatHistoryIndex() {
        const index = loadChatIndex();
        renderHistoryList(index);
        if (currentChatId) setActiveHistoryItem(currentChatId);
    }

    // === NEW Function to Handle Delete Click ===
    function handleDeleteChat(event) {
        event.stopPropagation(); // Prevent triggering loadChat on the link behind it
        const button = event.currentTarget;
        const chatIdToDelete = button.dataset.chatId;

        if (!chatIdToDelete) return;

        // Confirmation dialog
        if (
            window.confirm(
                `Are you sure you want to delete this chat session?\n"${
                    button.previousElementSibling?.textContent || "Chat " + chatIdToDelete
                }"`
            )
        ) {
            console.log(`Deleting chat: ${chatIdToDelete}`);

            // Perform deletion
            const updatedIndex = deleteChatData(chatIdToDelete);

            // If the deleted chat was the currently active one, load another chat
            if (currentChatId === chatIdToDelete) {
                currentChatId = null; // Reset current ID
                conversationHistory = []; // Clear state
                if (updatedIndex.length > 0) {
                    // Load the new top chat (most recent remaining)
                    loadChat(updatedIndex[0].id);
                } else {
                    // No chats left, start a new one
                    handleNewChat();
                }
            } else {
                // If a different chat was deleted, just re-render the list
                renderHistoryList(updatedIndex);
                // Re-apply active state in case IDs shifted (though they shouldn't)
                setActiveHistoryItem(currentChatId);
            }
        }
    }

    // === NEW Function to Delete Chat Data ===
    function deleteChatData(chatId) {
        // Remove chat data
        localStorage.removeItem(CHAT_PREFIX + chatId);

        // Update index
        let index = loadChatIndex();
        index = index.filter((item) => item.id !== chatId);
        saveChatIndex(index);

        console.log(`Chat ${chatId} data and index entry removed.`);
        return index; // Return the updated index
    }

    // --- Virtual Scrolling Placeholder ---
    // NOTE: Virtual scrolling is complex. For now, we do direct rendering.
    // If performance becomes an issue with very long chats/history,
    // investigate libraries like 'simple-virtual-scroll' or 'virtual-scroller'.
    // You would replace parts of `renderChatMessages` and `renderHistoryList`
    // to work with the chosen library's API (providing data and item renderers).
    console.warn("Virtual scrolling not implemented. Performance may degrade with very long chat histories.");
});
