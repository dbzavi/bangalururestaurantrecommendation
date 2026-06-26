# Deployment Plan: RecommendRestaurant

This document outlines the end-to-end deployment strategy to take our application live on the public internet.

## 1. The Database Size Challenge
Currently, `zomato.db` is **574 MB** because it stores massive text blobs of customer reviews that our app doesn't actually use. GitHub has a strict 100 MB upload limit, meaning we cannot push the database to GitHub in its current state, which means Railway won't be able to access it.

**Solution:** Before deploying, we will modify `etl.py` to drop the unused `reviews_list` column. This will shrink the database down to < 5MB. We will then remove it from `.gitignore` so it gets pushed to GitHub safely.

## 2. Backend Deployment (Railway)
**Why Railway?** It offers seamless deployment for Python/FastAPI apps directly from GitHub without needing complex Docker configurations.

**Steps:**
1. **Root Configuration:** Ensure `requirements.txt` is in the root or accessible. Add a `Procfile` telling the server to run: 
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
2. **Environment Variables:** Manually paste your `GROQ_API_KEY` into the Railway dashboard.
3. **CORS Update:** Update `main.py`'s CORS settings to allow requests from anywhere (`*`) so the Vercel frontend can communicate with it.

## 3. Frontend Deployment (Vercel)
**Why Vercel?** It is the industry standard for fast, static frontend hosting and integrates flawlessly with GitHub.

**Steps:**
1. **Dynamic Backend URL:** The frontend currently has `http://127.0.0.1:8000/api/recommend` hardcoded in `index.html`. We will modify this to point to the new live Railway URL once Railway is deployed.
2. **Vercel Config:** Since our frontend is a pure, lightning-fast Vanilla JS `index.html` file, Vercel will instantly detect it as a static site and deploy it in seconds with zero build steps required.

## Verification
1. Test the shrunken SQLite database locally to ensure AI recommendations still work flawlessly.
2. Link GitHub to Railway and Vercel.
3. Verify the live Vercel URL successfully hits the live Railway backend.
