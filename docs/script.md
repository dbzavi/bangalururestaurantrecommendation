# Zomato AI Restaurant Recommendation Project Script

Welcome to the complete guide for the **Zomato AI Restaurant Recommendation System**. This document breaks down the entire project from end-to-end so you can understand exactly how everything connects and functions under the hood.

---

## 1. Project Overview
This project is an intelligent restaurant discovery application. It allows users to filter restaurants based on hard criteria (location, budget, rating) and soft criteria ("AI Preferences" like "a romantic spot with great waffles"). 

It combines traditional SQL database querying with advanced generative AI (Large Language Models) to return highly curated results.

## 2. Architecture Stack
- **Frontend:** Pure HTML, JavaScript, and TailwindCSS (via CDN). No heavy frameworks like React.
- **Backend:** Python using **FastAPI** for ultra-fast API routing.
- **Database:** **SQLite3** for lightweight, serverless data storage.
- **ORM:** **SQLAlchemy** to map Python objects to SQL rows.
- **AI Integration:** **Groq** (using Llama 3 models) for instantaneous AI reasoning.
- **Deployment:** **Railway** (Backend) and **Vercel** (Frontend).

---

## 3. The Data Pipeline (ETL)
**Location:** `data_pipeline/etl.py`

The project starts with a massive dataset of Zomato restaurants from Kaggle (`zomato.csv`). Because the raw CSV is messy, we have an ETL (Extract, Transform, Load) script that:
1. Reads the raw CSV.
2. Cleans the data (removes Nulls, formats strings, converts cost formats to numbers).
3. **Drops massive columns** (like `reviews_list` and `menu_item`) to shrink the database size from 574MB down to ~33MB so it can be deployed on standard cloud providers and pushed to GitHub.
4. Saves everything into a highly optimized SQLite database file (`zomato.db`).

---

## 4. The Backend Flow
**Location:** `backend/`

The backend is structured into distinct, modular files so concerns are separated:

### A. `database.py`
Sets up the connection to the SQLite `zomato.db` file. It dynamically finds the file path so it works perfectly regardless of whether it's running locally or deployed on Railway.

### B. `models.py`
Defines the SQLAlchemy structure. This tells Python exactly what columns exist in the database so Python can read the rows as objects.

### C. `schemas.py`
Defines the **Pydantic** models. While `models.py` talks to the Database, `schemas.py` talks to the Internet. It dictates the strict format that incoming JSON requests and outgoing JSON responses must follow.

### D. `crud.py` (Create, Read, Update, Delete)
Handles the pure SQL logic. It takes the user's hard filters (e.g., Budget < ₹2000, Rating > 4.0, Location = "Bellandur") and pulls the **Top 100** matching candidates out of the database instantly.

### E. `ai_service.py`
The "Brain" of the operation. It takes the candidate restaurants found by `crud.py` and the user's custom text (e.g., "Good lighting for photos") and sends a strict prompt to the Groq AI API. The AI evaluates the candidates, ranks the top 5, and writes a custom `ai_explanation` for each one.

### F. `main.py`
The orchestrator. It creates the `/api/recommend` endpoint. 
**The Flow:**
1. Receives request from Frontend.
2. Calls `crud.py` to get candidates from the DB.
3. If the user provided AI preferences, it sends the candidates to `ai_service.py` for AI enrichment.
4. If no AI preferences were provided (or if the AI times out), it falls back to just returning the top 5 database results instantly.
5. Returns the final curated JSON list to the frontend.

---

## 5. The Frontend Flow
**Location:** `frontend/index.html`

The frontend is a single HTML file engineered for maximum performance and gorgeous aesthetics.
- **Design:** Uses glassmorphism (translucent panels over a dark background) and dynamic Tailwind CSS utility classes.
- **Responsiveness:** On Desktop, it uses a side-by-side (`lg:flex-row`) layout. On Mobile (`<1024px`), it functions as a "Single-Page Application" (SPA) where submitting the form hides the form and brings up a dedicated Results View with a "Back to Search" button.
- **API Communication:** Uses Axios to send a POST request to the backend. It automatically detects if you are running on `localhost` or Vercel, and routes the API call to your local Python server or your live Railway server accordingly.

---

## 6. The Deployment Setup
Because this is a decoupled architecture (Frontend separated from Backend), they are hosted in two different places:

1. **Backend (Railway):** 
   - Uses the `Procfile` in the root directory: `web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Railway spins up a Linux container, reads `requirements.txt`, installs Python, and runs the FastAPI server.
   - It holds the SQLite database locally within the container.

2. **Frontend (Vercel):**
   - Vercel acts as a lightning-fast CDN. It takes the `index.html` file and hosts it globally. 
   - When a user visits the Vercel link, their browser downloads the HTML and makes API calls directly to the Railway backend URL.

## Summary
By combining raw SQL speed for filtering with LLM intelligence for nuanced ranking, this project demonstrates a highly advanced, production-ready full-stack application built for both speed and user experience.
