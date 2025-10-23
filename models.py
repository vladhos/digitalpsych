# models.py
from datetime import datetime
from typing import Optional, Dict
from sqlmodel import SQLModel, Field, Column, JSON

# Tabuľka pre odpovede GDT
class ResponseGDT(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_code: str = Field(index=True)
    answers: Dict[str, int] = Field(sa_column=Column(JSON))
    raw_total: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
