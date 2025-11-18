"""
Database Schemas for Gamified Early Digital Literacy App

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Core users
class Child(BaseModel):
    name: str = Field(..., description="Child name")
    age: int = Field(..., ge=3, le=10, description="Age in years")
    avatar: Optional[str] = Field(None, description="Avatar URL or preset key")
    level: int = Field(1, ge=1, description="Current level")
    xp: int = Field(0, ge=0, description="Experience points")
    stars: int = Field(0, ge=0, description="Stars collected")
    badges: List[str] = Field(default_factory=list, description="Badge ids earned")

class Activity(BaseModel):
    title: str
    topic: Literal[
        "keamanan_internet",
        "perangkat_digital",
        "etika_digital",
        "berpikir_kritis"
    ]
    kind: Literal["quiz", "puzzle", "memory", "sorting", "video"]
    difficulty: Literal["easy", "medium", "hard"]
    est_duration: int = Field(5, description="Estimated duration in minutes")
    points: int = Field(10, description="XP points on completion")
    stars_reward: int = Field(1, description="Stars rewarded")
    asset: Optional[str] = Field(None, description="Illustration/asset path")

class Progress(BaseModel):
    child_id: str
    activity_id: str
    accuracy: float = Field(..., ge=0.0, le=1.0)
    duration_sec: int = Field(..., ge=0)
    mistakes: int = Field(0, ge=0)
    completed: bool = True

class Badge(BaseModel):
    code: str
    label: str
    description: Optional[str] = None
    icon: Optional[str] = None

class RecommendationRequest(BaseModel):
    child_id: str
    last_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    last_duration_sec: Optional[int] = Field(None, ge=0)
    last_difficulty: Optional[str] = Field(None)
    preferred_topic: Optional[str] = Field(None)

class RecommendationResponse(BaseModel):
    next_difficulty: str
    reasoning: str
    suggested_topics: List[str]
    activities: List[dict] = []

# Parent/teacher report
class ReportFilter(BaseModel):
    child_id: str
    limit: Optional[int] = 20
