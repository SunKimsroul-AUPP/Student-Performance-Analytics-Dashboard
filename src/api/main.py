from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .router import router
from ..utils.config_loader import load_settings

settings = load_settings()

app = FastAPI(title=settings["app"]["title"])
app.include_router(router, prefix="/api")

# Serve static frontend at root
app.mount("/", StaticFiles(directory="static", html=True), name="static")