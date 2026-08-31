// ==== File: ai.js ====

class ApiHandler {
    constructor(apiKey = null) {
      this.apiKey = apiKey || localStorage.getItem("openai_api_key") || "";
      console.log("ApiHandler ready");
    }
  
    setApiKey(k) {
      this.apiKey = k.trim();
      if (this.apiKey) localStorage.setItem("openai_api_key", this.apiKey);
    }
  
    async *chatStream(messages, {model = "gpt-4o", temperature = 0.7} = {}) {
      if (!this.apiKey) throw new Error("OpenAI API key missing");
      const payload = {model, messages, stream: true, max_tokens: 1024};
      const controller = new AbortController();
  
      const res = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`OpenAI: ${res.statusText}`);
      const reader = res.body.getReader();
      const dec = new TextDecoder();
  
      let buf = "";
      while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        buf += dec.decode(value, {stream: true});
        for (const line of buf.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          if (line.includes("[DONE]")) return;
          const json = JSON.parse(line.slice(6));
          const delta = json.choices?.[0]?.delta?.content;
          if (delta) yield delta;
        }
        buf = buf.endsWith("\n") ? "" : buf; // keep partial line
      }
    }
  }
  
  window.API = new ApiHandler();
  