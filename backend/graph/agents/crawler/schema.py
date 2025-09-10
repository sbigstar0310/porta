# agents/crawler/schema.py
from pydantic import BaseModel
from typing import List


class NewCandidate(BaseModel):
    ticker: str
    name: str
    reason: str
    ref_url: List[str]


class CrawlerState(BaseModel):
    universe: List[str]
    asof: str
    new_candidates: List[NewCandidate] = []


class CrawlerOutput(BaseModel):
    new_candidates: List[NewCandidate]
