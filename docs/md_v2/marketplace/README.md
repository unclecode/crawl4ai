# Crawl4AI Marketplace

A terminal-themed marketplace for tools, integrations, and resources related to Crawl4AI.

## Setup

### Backend

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Generate dummy data:
```bash
python dummy_data.py
```

3. Run the server:
```bash
python server.py
```

The API will be available at http://localhost:8100

### Frontend

1. Open `frontend/index.html` in your browser
2. Or serve via MkDocs as part of the documentation site

## Database Schema

The marketplace uses SQLite with automatic migration from `schema.yaml`. Tables include:
- **apps**: Tools and integrations
- **articles**: Reviews, tutorials, and news
- **categories**: App categories
- **sponsors**: Sponsored content

## API Endpoints

- `GET /api/apps` - List apps with filters
- `GET /api/articles` - List articles
- `GET /api/categories` - Get all categories
- `GET /api/sponsors` - Get active sponsors
- `GET /api/search?q=query` - Search across content
- `GET /api/stats` - Marketplace statistics

## Features

- **Smart caching**: LocalStorage with TTL (1 hour)
- **Terminal theme**: Consistent with Crawl4AI branding
- **Responsive design**: Works on all devices
- **Fast search**: Debounced with 300ms delay
- **CORS protected**: Only crawl4ai.com and localhost

## Admin Panel

Coming soon - for now, edit the database directly or modify `dummy_data.py`

## Deployment

For production deployment on EC2:
1. Update `API_BASE` in `marketplace.js` to production URL
2. Run FastAPI with proper production settings (use gunicorn/uvicorn)
3. Set up nginx proxy if needed