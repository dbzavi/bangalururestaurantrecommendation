from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import models, schemas

def get_candidate_restaurants(db: Session, prefs: schemas.RecommendationRequest):
    query = db.query(models.Restaurant)

    # 1. Budget Filter
    query = query.filter(models.Restaurant.cost_for_two <= prefs.budget_max)

    # 2. Rating Filter
    query = query.filter(models.Restaurant.rate >= prefs.min_rating)

    # 3. Location Filter (Strict match on physical location)
    if prefs.location and prefs.location.lower() not in ["any", "all", "anywhere"]:
        loc_pattern = f"%{prefs.location}%"
        query = query.filter(models.Restaurant.location.ilike(loc_pattern))

    # 4. Cuisine Filter (Fuzzy match ANY of the requested cuisines)
    if prefs.cuisines:
        cuisine_conditions = []
        for cuisine in prefs.cuisines:
            cuisine_conditions.append(models.Restaurant.cuisines.ilike(f"%{cuisine}%"))
        query = query.filter(or_(*cuisine_conditions))

    # 5. Order and Limit (fetch more to allow deduplication)
    query = query.order_by(models.Restaurant.rate.desc(), models.Restaurant.votes.desc())
    
    raw_candidates = query.limit(100).all()
    
    # Deduplicate by name and location
    seen = set()
    candidates = []
    for r in raw_candidates:
        identifier = (r.name.lower(), r.location.lower())
        if identifier not in seen:
            seen.add(identifier)
            candidates.append(r)
            if len(candidates) == 20:
                break
                
    return candidates
