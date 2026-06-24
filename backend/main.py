from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Union

import models, schemas, crud, ai_service
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zomato AI Restaurant Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/recommend", response_model=List[Union[schemas.RankedRestaurantResponse, schemas.RestaurantResponse]])
async def get_recommendations(prefs: schemas.RecommendationRequest, db: Session = Depends(get_db)):
    """
    Phase 3 Endpoint:
    Queries SQLite for top 20 candidates. 
    If 'additional_preferences' are provided, asks Groq LLM to rank and explain the top 5.
    Otherwise, returns the top 5 directly from the DB.
    """
    # 1. First-pass retrieval from SQLite
    candidates = crud.get_candidate_restaurants(db, prefs)
    
    if not candidates:
        raise HTTPException(status_code=404, detail="No restaurants found matching your hard constraints.")

    # 2. AI Integration (Phase 3)
    if prefs.additional_preferences:
        try:
            # Send to Groq
            rankings_map = await ai_service.get_llm_ranking(candidates, prefs.additional_preferences)
            
            # Merge AI data with DB objects
            enriched_candidates = []
            for c in candidates:
                if c.zomato_url in rankings_map:
                    # Convert SQLAlchemy model to dict, then add AI fields
                    c_dict = {col.name: getattr(c, col.name) for col in c.__table__.columns}
                    c_dict["ai_rank"] = rankings_map[c.zomato_url]["ai_rank"]
                    c_dict["ai_explanation"] = rankings_map[c.zomato_url]["ai_explanation"]
                    enriched_candidates.append(c_dict)
            
            # Sort by AI rank
            enriched_candidates.sort(key=lambda x: x["ai_rank"])
            
            # Re-index to ensure strictly sequential numbers (1, 2, 3, 4...)
            for idx, candidate in enumerate(enriched_candidates):
                candidate["ai_rank"] = idx + 1
            
            # Verify we got results back
            if not enriched_candidates:
                raise HTTPException(status_code=500, detail="LLM failed to match any candidates.")
                
            return enriched_candidates
            
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            # Fallback in case of API error
            print(f"LLM Error: {e}")
            return candidates[:5]
    else:
        # Fallback if no specific AI preferences provided
        return candidates[:5]

@app.get("/")
def root():
    return {"message": "Welcome to the Zomato AI Recommendation API! Use POST /api/recommend"}
