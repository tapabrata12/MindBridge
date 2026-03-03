from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.health_routes import router_health
from src.routes.screening_routes import router_screening
from src.core.config import settings
import uvicorn
app = FastAPI(title="Mental Health Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)
app.include_router(router_health)
app.include_router(router_screening)

if __name__ == "__main__":

    uvicorn.run("main:app", port=8000, reload=True)