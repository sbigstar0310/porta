# backend/routers/agent_feedback.py
from fastapi import APIRouter
from graph.app import run_graph

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run")
async def post_agent_feedback():
    run_graph()
