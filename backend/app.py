import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db_init import init_db
from routes import agent, activity, cost, tasks, crons, agent_pipeline, portfolio
from agents_runner import init_agents_runner

logger = logging.getLogger(__name__)

init_db()

app = FastAPI(title="Mission Control API")

# CORS for dev and preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:4173", "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(agent.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(cost.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(crons.router, prefix="/api")
app.include_router(agent_pipeline.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize and start the agents pipeline on app startup."""
    user_phone = os.getenv("USER_PHONE_NUMBER", "")
    agents_runner = init_agents_runner(user_phone_number=user_phone)
    agents_runner.start()
    logger.info("Agents pipeline started successfully")


@app.get("/health")
def health():
    return {"status": "ok"}

# Serve frontend
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
