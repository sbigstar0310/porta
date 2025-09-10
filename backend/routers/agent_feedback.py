# backend/routers/agent_feedback.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_session, Settings
from graph.app import run_graph

router = APIRouter(prefix="/agent-feedback", tags=["agent-feedback"])
settings = Settings()


@router.post("")
async def post_agent_feedback(session: AsyncSession = Depends(get_session)):
    run_graph()
