from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.elasticsearch import close_es_client
from app.tasks.scheduler import start_scheduler, stop_scheduler

from app.core.logging import setup_logging

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()
    await close_es_client()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {
            "message": f"{settings.app_name} is running",
            "version": "1.0.0",
            "status": "healthy"
        }

    @app.get("/health")
    async def health_check():
        from app.core.database import engine
        from sqlalchemy import text
        import logging
        health_logger = logging.getLogger("health")
        
        db_status = "ok"
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            health_logger.error(f"Health Check - DB Error: {e}")

        return {
            "status": "healthy" if "unhealthy" not in db_status else "degraded",
            "database": db_status,
            "app": "running"
        }

    # Unified Exception Handling
    from fastapi import Request, HTTPException
    from fastapi.responses import JSONResponse
    import logging
    
    logger = logging.getLogger(__name__)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        from app.utils.responses import response_error
        # Format HTTP status correctly to unify with custom exception formats
        return JSONResponse(
            status_code=exc.status_code,
            content=response_error(
                message=str(exc.detail),
                error=exc.detail
            ),
            headers=exc.headers
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        from app.utils.responses import response_error
        logger.error(f"Global Error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=response_error(
                message="服务器内部错误",
                error=str(exc) if settings.debug else "Internal Server Error"
            ),
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
