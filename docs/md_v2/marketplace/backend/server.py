from fastapi import FastAPI, HTTPException, Query, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
import json
import hashlib
import secrets
from database import DatabaseManager
from datetime import datetime, timedelta

# Import configuration (will exit if .env not found or invalid)
from config import Config

app = FastAPI(title="Crawl4AI Marketplace API")

# Security setup
security = HTTPBearer()
tokens = {}  # In production, use Redis or database for token storage

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600
)

# Initialize database with configurable path
db = DatabaseManager(Config.DATABASE_PATH)

def json_response(data, cache_time=3600):
    """Helper to return JSON with cache headers"""
    return JSONResponse(
        content=data,
        headers={
            "Cache-Control": f"public, max-age={cache_time}",
            "X-Content-Type-Options": "nosniff"
        }
    )

# ============= PUBLIC ENDPOINTS =============

@app.get("/api/apps")
async def get_apps(
    category: Optional[str] = None,
    type: Optional[str] = None,
    featured: Optional[bool] = None,
    sponsored: Optional[bool] = None,
    limit: int = Query(default=20, le=10000),
    offset: int = Query(default=0)
):
    """Get apps with optional filters"""
    where_clauses = []
    if category:
        where_clauses.append(f"category = '{category}'")
    if type:
        where_clauses.append(f"type = '{type}'")
    if featured is not None:
        where_clauses.append(f"featured = {1 if featured else 0}")
    if sponsored is not None:
        where_clauses.append(f"sponsored = {1 if sponsored else 0}")

    where = " AND ".join(where_clauses) if where_clauses else None
    apps = db.get_all('apps', limit=limit, offset=offset, where=where)

    # Parse JSON fields
    for app in apps:
        if app.get('screenshots'):
            app['screenshots'] = json.loads(app['screenshots'])

    return json_response(apps)

@app.get("/api/apps/{slug}")
async def get_app(slug: str):
    """Get single app by slug"""
    apps = db.get_all('apps', where=f"slug = '{slug}'", limit=1)
    if not apps:
        raise HTTPException(status_code=404, detail="App not found")

    app = apps[0]
    if app.get('screenshots'):
        app['screenshots'] = json.loads(app['screenshots'])

    return json_response(app)

@app.get("/api/articles")
async def get_articles(
    category: Optional[str] = None,
    limit: int = Query(default=20, le=10000),
    offset: int = Query(default=0)
):
    """Get articles with optional category filter"""
    where = f"category = '{category}'" if category else None
    articles = db.get_all('articles', limit=limit, offset=offset, where=where)

    # Parse JSON fields
    for article in articles:
        if article.get('related_apps'):
            article['related_apps'] = json.loads(article['related_apps'])
        if article.get('tags'):
            article['tags'] = json.loads(article['tags'])

    return json_response(articles)

@app.get("/api/articles/{slug}")
async def get_article(slug: str):
    """Get single article by slug"""
    articles = db.get_all('articles', where=f"slug = '{slug}'", limit=1)
    if not articles:
        raise HTTPException(status_code=404, detail="Article not found")

    article = articles[0]
    if article.get('related_apps'):
        article['related_apps'] = json.loads(article['related_apps'])
    if article.get('tags'):
        article['tags'] = json.loads(article['tags'])

    return json_response(article)

@app.get("/api/categories")
async def get_categories():
    """Get all categories ordered by index"""
    categories = db.get_all('categories', limit=50)
    categories.sort(key=lambda x: x.get('order_index', 0))
    return json_response(categories, cache_time=7200)

@app.get("/api/sponsors")
async def get_sponsors(active: Optional[bool] = True):
    """Get sponsors, default active only"""
    where = f"active = {1 if active else 0}" if active is not None else None
    sponsors = db.get_all('sponsors', where=where, limit=20)

    # Filter by date if active
    if active:
        now = datetime.now().isoformat()
        sponsors = [s for s in sponsors
                   if (not s.get('start_date') or s['start_date'] <= now) and
                      (not s.get('end_date') or s['end_date'] >= now)]

    return json_response(sponsors)

@app.get("/api/search")
async def search(q: str = Query(min_length=2)):
    """Search across apps and articles"""
    if len(q) < 2:
        return json_response({})

    results = db.search(q, tables=['apps', 'articles'])

    # Parse JSON fields in results
    for table, items in results.items():
        for item in items:
            if table == 'apps' and item.get('screenshots'):
                item['screenshots'] = json.loads(item['screenshots'])
            elif table == 'articles':
                if item.get('related_apps'):
                    item['related_apps'] = json.loads(item['related_apps'])
                if item.get('tags'):
                    item['tags'] = json.loads(item['tags'])

    return json_response(results, cache_time=1800)

@app.get("/api/stats")
async def get_stats():
    """Get marketplace statistics"""
    stats = {
        "total_apps": len(db.get_all('apps', limit=10000)),
        "total_articles": len(db.get_all('articles', limit=10000)),
        "total_categories": len(db.get_all('categories', limit=1000)),
        "active_sponsors": len(db.get_all('sponsors', where="active = 1", limit=1000))
    }
    return json_response(stats, cache_time=1800)

# ============= ADMIN AUTHENTICATION =============

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin authentication token"""
    token = credentials.credentials
    if token not in tokens or tokens[token] < datetime.now():
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token

@app.post("/api/admin/login")
async def admin_login(password: str = Body(..., embed=True)):
    """Admin login with password"""
    provided_hash = hashlib.sha256(password.encode()).hexdigest()

    if provided_hash != Config.ADMIN_PASSWORD_HASH:
        # Log failed attempt in production
        print(f"Failed login attempt at {datetime.now()}")
        raise HTTPException(status_code=401, detail="Invalid password")

    # Generate secure token
    token = secrets.token_urlsafe(32)
    tokens[token] = datetime.now() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS)

    return {
        "token": token,
        "expires_in": Config.TOKEN_EXPIRY_HOURS * 3600
    }

# ============= ADMIN ENDPOINTS =============

@app.get("/api/admin/stats", dependencies=[Depends(verify_token)])
async def get_admin_stats():
    """Get detailed admin statistics"""
    stats = {
        "apps": {
            "total": len(db.get_all('apps', limit=10000)),
            "featured": len(db.get_all('apps', where="featured = 1", limit=10000)),
            "sponsored": len(db.get_all('apps', where="sponsored = 1", limit=10000))
        },
        "articles": len(db.get_all('articles', limit=10000)),
        "categories": len(db.get_all('categories', limit=1000)),
        "sponsors": {
            "active": len(db.get_all('sponsors', where="active = 1", limit=1000)),
            "total": len(db.get_all('sponsors', limit=10000))
        },
        "total_views": sum(app.get('views', 0) for app in db.get_all('apps', limit=10000))
    }
    return stats

# Apps CRUD
@app.post("/api/admin/apps", dependencies=[Depends(verify_token)])
async def create_app(app_data: Dict[str, Any]):
    """Create new app"""
    try:
        # Handle JSON fields
        for field in ['screenshots', 'tags']:
            if field in app_data and isinstance(app_data[field], list):
                app_data[field] = json.dumps(app_data[field])

        cursor = db.conn.cursor()
        columns = ', '.join(app_data.keys())
        placeholders = ', '.join(['?' for _ in app_data])
        cursor.execute(f"INSERT INTO apps ({columns}) VALUES ({placeholders})",
                      list(app_data.values()))
        db.conn.commit()
        return {"id": cursor.lastrowid, "message": "App created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/apps/{app_id}", dependencies=[Depends(verify_token)])
async def update_app(app_id: int, app_data: Dict[str, Any]):
    """Update app"""
    try:
        # Handle JSON fields
        for field in ['screenshots', 'tags']:
            if field in app_data and isinstance(app_data[field], list):
                app_data[field] = json.dumps(app_data[field])

        set_clause = ', '.join([f"{k} = ?" for k in app_data.keys()])
        cursor = db.conn.cursor()
        cursor.execute(f"UPDATE apps SET {set_clause} WHERE id = ?",
                      list(app_data.values()) + [app_id])
        db.conn.commit()
        return {"message": "App updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/admin/apps/{app_id}", dependencies=[Depends(verify_token)])
async def delete_app(app_id: int):
    """Delete app"""
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM apps WHERE id = ?", (app_id,))
    db.conn.commit()
    return {"message": "App deleted"}

# Articles CRUD
@app.post("/api/admin/articles", dependencies=[Depends(verify_token)])
async def create_article(article_data: Dict[str, Any]):
    """Create new article"""
    try:
        for field in ['related_apps', 'tags']:
            if field in article_data and isinstance(article_data[field], list):
                article_data[field] = json.dumps(article_data[field])

        cursor = db.conn.cursor()
        columns = ', '.join(article_data.keys())
        placeholders = ', '.join(['?' for _ in article_data])
        cursor.execute(f"INSERT INTO articles ({columns}) VALUES ({placeholders})",
                      list(article_data.values()))
        db.conn.commit()
        return {"id": cursor.lastrowid, "message": "Article created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/articles/{article_id}", dependencies=[Depends(verify_token)])
async def update_article(article_id: int, article_data: Dict[str, Any]):
    """Update article"""
    try:
        for field in ['related_apps', 'tags']:
            if field in article_data and isinstance(article_data[field], list):
                article_data[field] = json.dumps(article_data[field])

        set_clause = ', '.join([f"{k} = ?" for k in article_data.keys()])
        cursor = db.conn.cursor()
        cursor.execute(f"UPDATE articles SET {set_clause} WHERE id = ?",
                      list(article_data.values()) + [article_id])
        db.conn.commit()
        return {"message": "Article updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/admin/articles/{article_id}", dependencies=[Depends(verify_token)])
async def delete_article(article_id: int):
    """Delete article"""
    cursor = db.conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    db.conn.commit()
    return {"message": "Article deleted"}

# Categories CRUD
@app.post("/api/admin/categories", dependencies=[Depends(verify_token)])
async def create_category(category_data: Dict[str, Any]):
    """Create new category"""
    try:
        cursor = db.conn.cursor()
        columns = ', '.join(category_data.keys())
        placeholders = ', '.join(['?' for _ in category_data])
        cursor.execute(f"INSERT INTO categories ({columns}) VALUES ({placeholders})",
                      list(category_data.values()))
        db.conn.commit()
        return {"id": cursor.lastrowid, "message": "Category created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/categories/{cat_id}", dependencies=[Depends(verify_token)])
async def update_category(cat_id: int, category_data: Dict[str, Any]):
    """Update category"""
    try:
        set_clause = ', '.join([f"{k} = ?" for k in category_data.keys()])
        cursor = db.conn.cursor()
        cursor.execute(f"UPDATE categories SET {set_clause} WHERE id = ?",
                      list(category_data.values()) + [cat_id])
        db.conn.commit()
        return {"message": "Category updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Sponsors CRUD
@app.post("/api/admin/sponsors", dependencies=[Depends(verify_token)])
async def create_sponsor(sponsor_data: Dict[str, Any]):
    """Create new sponsor"""
    try:
        cursor = db.conn.cursor()
        columns = ', '.join(sponsor_data.keys())
        placeholders = ', '.join(['?' for _ in sponsor_data])
        cursor.execute(f"INSERT INTO sponsors ({columns}) VALUES ({placeholders})",
                      list(sponsor_data.values()))
        db.conn.commit()
        return {"id": cursor.lastrowid, "message": "Sponsor created"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/admin/sponsors/{sponsor_id}", dependencies=[Depends(verify_token)])
async def update_sponsor(sponsor_id: int, sponsor_data: Dict[str, Any]):
    """Update sponsor"""
    try:
        set_clause = ', '.join([f"{k} = ?" for k in sponsor_data.keys()])
        cursor = db.conn.cursor()
        cursor.execute(f"UPDATE sponsors SET {set_clause} WHERE id = ?",
                      list(sponsor_data.values()) + [sponsor_id])
        db.conn.commit()
        return {"message": "Sponsor updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "Crawl4AI Marketplace API",
        "version": "1.0.0",
        "endpoints": [
            "/api/apps",
            "/api/articles",
            "/api/categories",
            "/api/sponsors",
            "/api/search?q=query",
            "/api/stats"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8100)