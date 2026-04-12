from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from infra_docker import DockerClient
from routers import health, services


@asynccontextmanager
async def lifespan(app: FastAPI):
    DockerClient.initialize()
    yield
    DockerClient.close()


app = FastAPI(
    title="Infra Hub API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(services.router, prefix="/api", tags=["Services"])


@app.get("/")
async def root():
    return {"message": "Infra Hub API", "docs": "/docs"}
