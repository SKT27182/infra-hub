from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from config import settings
from infra_docker import DockerClient
from routers import health, services, auth
from services.user_db import UserStoreUnavailableError, user_service
from services.auth import auth_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    DockerClient.initialize()
    await user_service.ensure_user_table()
    yield
    DockerClient.close()


app = FastAPI(
    title="Infra Hub API",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

security = HTTPBasic()


async def get_docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """Check basic auth for documentation."""
    try:
        user = await user_service.get_user_by_email(credentials.username)
    except UserStoreUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Documentation authentication is unavailable because the user database is unreachable.",
        ) from exc

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not auth_service.verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/docs", include_in_schema=False)
async def get_documentation(username: str = Depends(get_docs_auth)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Infra Hub API Docs")


@app.get("/openapi.json", include_in_schema=False)
async def openapi_endpoint(username: str = Depends(get_docs_auth)):
    return get_openapi(title=app.title, version="0.1.0", routes=app.routes)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(services.router, prefix="/api", tags=["Services"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])


@app.get("/")
async def root():
    return {"message": "Infra Hub API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
