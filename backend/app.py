# backend/main.py
from dotenv import load_dotenv
from fastapi import FastAPI
import os
from db import init_database
from routers.portfolio import router as portfolio_router

app = FastAPI(title="PORTA")

# EXPORT ENV VARIABLES
load_dotenv()

# API KEYS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


@app.on_event("startup")
async def on_startup():
    await init_database()


app.include_router(portfolio_router)


@app.get("/health")
async def health():
    return {"ok": True}
