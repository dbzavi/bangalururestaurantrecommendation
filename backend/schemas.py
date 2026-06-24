from pydantic import BaseModel, Field
from typing import List, Optional

class RecommendationRequest(BaseModel):
    location: str = Field(..., description="The city or neighborhood")
    budget_max: int = Field(..., description="Maximum budget for two people")
    cuisines: List[str] = Field(default_factory=list, description="List of preferred cuisines")
    min_rating: float = Field(default=0.0, description="Minimum acceptable rating (0 to 5)")
    additional_preferences: str = Field(default="", description="Any free-text soft constraints like 'romantic' or 'vegan'")

class RestaurantResponse(BaseModel):
    zomato_url: str
    name: str
    location: str
    cuisines: str
    cost_for_two: float
    rate: float
    votes: int
    
    class Config:
        from_attributes = True

class RankedRestaurantResponse(RestaurantResponse):
    ai_rank: int
    ai_explanation: str

