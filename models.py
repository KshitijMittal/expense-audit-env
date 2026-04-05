from pydantic import BaseModel, field_validator
from typing import List, Optional


# What AI sees
class Observation(BaseModel):
    task_id: str
    task_description: str

    item_name: str
    amount: float
    category: str
    vendor: str
    date_of_expense: str
    date_submitted: str

    policy: str
    history: List[str]


# What AI sends back
class Action(BaseModel):
    decision: str  # "approve", "reject", "escalate"
    reason: Optional[str] = None

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value):
        value = value.lower()
        allowed = {"approve", "reject", "escalate"}

        if value not in allowed:
            raise ValueError(f"Decision must be one of {allowed}")

        return value

# What environment returns
class Reward(BaseModel):
    score: float
    explanation: str
    done: bool
    confidence: float = 1.0