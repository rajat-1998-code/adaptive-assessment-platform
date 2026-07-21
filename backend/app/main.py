from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middleware

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the Adaptive RAG-Powered Assessment & Learning Platform",
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_middleware(app)
register_exception_handlers(app)

app.include_router(router)


@app.get("/")
def read_root():
    """Basic root endpoint to confirm the API is running."""
    return {"message": f"{settings.APP_NAME} API is running"}
