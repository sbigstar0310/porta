# agents/reviewer/schema.py
from pydantic import BaseModel


class ReviewerNote(BaseModel):
    period: str
    opinion: str
    preference: str
    adjustment: float


class ReviewerState(BaseModel):
    user_id: int
    asof: str
    review_note: ReviewerNote | None = None


class ReviewerOutput(BaseModel):
    review_note: ReviewerNote
