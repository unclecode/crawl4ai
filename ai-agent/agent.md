You are building the backend crawling service that will be deployed on Railway. This service receives crawl requests from a Next.js/Convex frontend, processes them, and returns structured content for a RAG chatbot system.

### Architecture Context

```
Frontend (Next.js/Convex) → YOUR SERVICE (Railway) → Returns Clean Content → RAG Pipeline

┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│  Next.js + TypeScript + ShadcN + Zod            │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Convex Backend                      │
│  - Real-time subscriptions                       │
│  - User management                               │
│  - Chat history                                  │
│  - RAG knowledge base                           │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          Convex Actions/HTTP                     │
│  - Call Railway crawler service                  │
│  - Manage crawl jobs                            │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│      Railway Crawler Service                     │
│  - Your deployed crawler                         │
│  - Redis for queue/cache                        │
└──────────────────────────────────────────────────┘
```

### Technology Stack for Your Component

- **Language:** Python 3.11.1
- **Framework:** FastAPI
- **Crawler:** Simple httpx + BeautifulSoup (no Playwright/crawl4ai initially)
- **Queue:** Redis (Railway addon)
- **Deployment:** Railway
- **Monitoring:** Built-in metrics endpoi
