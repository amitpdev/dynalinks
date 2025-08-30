from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.openapi.utils import get_openapi
import time
import uvicorn
from contextlib import asynccontextmanager

from app.config import settings
from app.db_pg import get_db_instance
from app.routers import links, redirect, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_db_instance()
    yield
    # Shutdown
    db = await get_db_instance()
    await db.disconnect()

# Initialize FastAPI app
app = FastAPI(
    title="DynaLinks - Dynamic Link Service",
    description="A Firebase Dynamic Links alternative - URL shortener with platform-specific redirects",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.debug:
        raise exc
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Rate limiting middleware (basic implementation)
request_counts = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    cutoff_time = current_time - 60
    request_counts[client_ip] = [
        timestamp for timestamp in request_counts.get(client_ip, [])
        if timestamp > cutoff_time
    ]
    
    # Check rate limit
    if len(request_counts.get(client_ip, [])) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Add current request
    request_counts.setdefault(client_ip, []).append(current_time)
    
    response = await call_next(request)
    return response

# Include routers
app.include_router(links.router)
app.include_router(redirect.router)
app.include_router(health.router)

# Favicon routes to prevent 404 logs from browsers
@app.get("/favicon.ico")
@app.get("/{short_code}/favicon.ico")
async def favicon():
    """Handle favicon requests to prevent 404 logs."""
    return Response(status_code=204)  # No Content

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="DynaLinks API",
        version="1.0.0",
        description="Dynamic Link Service API - Create and manage short links with platform-specific redirects",
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )