from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.mongodb import connect_to_mongo,close_mongo_connection
from src.api.routes.auth import router as auth_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    print("MongoDB connected ✅")
    yield
    await close_mongo_connection()
    print("MongoDB disconnected ✅")

# Create an instance of the FastAPI app
app = FastAPI(lifespan=lifespan)

"""
Including every type of routes into the `main.py`
"""
app.include_router(auth_router)