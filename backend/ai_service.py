import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def get_llm_ranking(candidates: list, user_preferences: str):
    """
    Takes a list of candidate dictionaries (from DB) and user preferences,
    and calls Groq to get the top 5 ranked restaurants with explanations.
    Returns a dictionary mapping zomato_url -> {"ai_rank": int, "ai_explanation": str}
    """
    if not GROQ_API_KEY or GROQ_API_KEY == "your_api_key_here":
        raise ValueError("GROQ_API_KEY is missing or invalid.")

    # Serialize candidates to a lightweight JSON string to save context window
    compact_candidates = []
    for c in candidates:
        compact_candidates.append({
            "zomato_url": c.zomato_url,
            "name": c.name,
            "cuisines": c.cuisines,
            "cost_for_two": c.cost_for_two,
            "rate": c.rate,
            "votes": c.votes
        })
    
    candidates_json = json.dumps(compact_candidates)

    system_prompt = """You are an expert food critic and local restaurant guide. 
You are given a JSON list of candidate restaurants and the user's highly specific preferences.
Your task is to rank exactly the top 5 restaurants that best match the user's nuanced preferences.
You MUST output your response in strict JSON format. 
The JSON must have a single root key called 'rankings' containing an array of exactly 5 objects.
Each object must have:
- 'zomato_url': the exact zomato_url of the restaurant
- 'ai_rank': integer from 1 to 5
- 'ai_explanation': 1-2 sentences explaining why this restaurant fits the user's specific preferences."""

    user_prompt = f"""User Preferences: {user_preferences}

Candidate Restaurants:
{candidates_json}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )
    
    if response.status_code != 200:
        raise Exception(f"Groq API Error: {response.text}")
        
    result_data = response.json()
    llm_output = json.loads(result_data["choices"][0]["message"]["content"])
    
    # Map the output back to a dictionary for easy merging
    rankings_map = {}
    for item in llm_output.get("rankings", []):
        url = item.get("zomato_url")
        if url:
            rankings_map[url] = {
                "ai_rank": item.get("ai_rank"),
                "ai_explanation": item.get("ai_explanation")
            }
            
    return rankings_map
