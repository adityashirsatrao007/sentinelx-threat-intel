from pydantic import BaseModel
from typing import List

class TargetMetric(BaseModel):
    name: str
    threat_count: int
    avg_risk_score: float

class TargetAnalyticsResponse(BaseModel):
    departments: List[TargetMetric]
    roles: List[TargetMetric]
