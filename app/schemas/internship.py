from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class InternshipBase(BaseModel):
    title: str
    description: str
    fee_amount: float
    tech_stack: List[str]

class InternshipResponse(InternshipBase):
    id: UUID

    class Config:
        from_attributes = True