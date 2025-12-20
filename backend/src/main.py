"""
FastAPI main application.
Initializes the API, middleware, and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.logging import setup_logging, get_logger, set_request_id
from .core.database import check_db_connection
from .core.redis_client import redis_client

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal Stock Screener with Sentiment Analysis for Indian Equities",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = request.headers.get("X-Request-ID")
    set_request_id(request_id)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = set_request_id()
    
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection verified")
    else:
        logger.error("Database connection failed!")
    
    # Check Redis connection
    if redis_client.check_connection():
        logger.info("Redis connection verified")
    else:
        logger.warning("Redis connection failed!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application...")
    redis_client.close()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    db_healthy = check_db_connection()
    redis_healthy = redis_client.check_connection()
    
    status = "healthy" if (db_healthy and redis_healthy) else "unhealthy"
    status_code = 200 if status == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "version": settings.APP_VERSION
        }
    )


# Import and include routers
from .api.v1 import stocks, screening, alerts

app.include_router(
    stocks.router,
    prefix=f"{settings.API_V1_PREFIX}/stocks",
    tags=["Stocks"]
)

app.include_router(
    screening.router,
    prefix=f"{settings.API_V1_PREFIX}/screen",
    tags=["Screening"]
)

app.include_router(
    alerts.router,
    prefix=f"{settings.API_V1_PREFIX}/alerts",
    tags=["Alerts"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
