# Zomato AI Restaurant Recommendation Project: Technical Deep-Dive

Welcome to the comprehensive technical documentation for the **Zomato AI Restaurant Recommendation System**. This document provides an in-depth look into the architecture, data flow, engineering decisions, and codebase structure of the project. It is designed to help developers, reviewers, and stakeholders understand the complete lifecycle of the application.

---

## 1. Executive Summary
The goal of this project is to create a blazing-fast, intelligent restaurant discovery engine. Standard filters (location, budget, rating) are often insufficient for users seeking a specific "vibe" or highly specialized criteria. 

By marrying traditional **Relational Database filtering (SQLite/SQLAlchemy)** with **Generative AI (Groq/Llama 3)**, this system can instantly filter out thousands of irrelevant restaurants and then use human-like reasoning to curate the final top 5 recommendations based on custom user prompts (e.g., *"Looking for a quiet, romantic spot with vintage decor"*).

---

## 2. System Architecture & Tech Stack

The application uses a decoupled architecture where the frontend and backend operate entirely independently, communicating strictly via REST APIs.

### Backend (API Engine)
- **Framework:** FastAPI (Python) - Chosen for its asynchronous capabilities, auto-generated OpenAPI documentation, and extreme speed.
- **Database:** SQLite3 - A serverless, file-based database ideal for read-heavy, read-only analytics workloads.
- **ORM:** SQLAlchemy - Used for safe, Pythonic database querying without writing raw SQL.
- **AI Provider:** Groq (Llama 3 8B/70B models) - Chosen for its unparalleled inference speed (Language Processing Unit architecture), allowing AI reasoning without forcing the user to wait on long loading screens.

### Frontend (User Interface)
- **Core:** Pure HTML5, Vanilla JavaScript. (No React/Vue required, keeping the bundle size negligible).
- **Styling:** TailwindCSS (via CDN) - Used for rapid utility-class styling and modern "Glassmorphism" aesthetics.
- **Networking:** Axios - Used to handle asynchronous API POST requests to the backend.

### Deployment Infrastructure
- **Backend Hosting:** Railway.app (Containerized execution).
- **Frontend Hosting:** Vercel (Global Edge CDN for static assets).

---

## 3. The Data Pipeline (ETL Phase)
**Location:** `data_pipeline/etl.py`

The system relies on a static snapshot of Zomato restaurant data. The raw dataset (`zomato.csv`) is enormous and contains messy, unstructured data. The ETL (Extract, Transform, Load) script acts as the data cleaner.

**Key Operations:**
1. **Extraction:** Loads the raw Kaggle CSV using the `pandas` library.
2. **Transformation (Cleaning):**
   - Renames columns to standardized snake_case formats.
   - Cleans the `cost_for_two` string (e.g., `"1,200"`) into standard integers (`1200`).
   - Converts the `rate` string (e.g., `"4.1/5"`) into a float (`4.1`).
   - Fills missing boolean values (`online_order`, `book_table`) with 'No'.
3. **Transformation (Optimization):**
   - **Crucial Step:** The raw dataset includes a `reviews_list` column containing massive text blobs of user reviews. This inflated the database size to over **574 MB**, exceeding GitHub's file limits and increasing RAM usage. The ETL script explicitly drops `reviews_list` and `menu_item`, shrinking the database to a highly portable **33 MB**.
4. **Loading:** Uses `sqlite3` to create `zomato.db` and writes the cleaned DataFrame directly into a highly indexed SQL table.

---

## 4. Backend Implementation Details
**Location:** `backend/`

The backend is strictly modularized. Each file has a distinct responsibility.

### `database.py` (Connection Management)
Initializes the SQLAlchemy Engine. 
*Engineering Note:* Because deployment environments (like Railway) can launch the application from different root directories, `database.py` uses `os.path.abspath(__file__)` to dynamically resolve the absolute path to `zomato.db`. This prevents "File Not Found" errors in production.

### `models.py` (Data Layer)
Defines the `Restaurant` class inheriting from SQLAlchemy's `Base`. It maps Python data types to SQLite column types. Indexes are placed on `location`, `cost_for_two`, and `rate` to ensure sub-millisecond query performance.

### `schemas.py` (Validation Layer)
Uses Pydantic to enforce strict type-checking on data entering and leaving the API. 
- `RecommendationRequest`: Validates incoming search parameters.
- `RestaurantResponse`: Defines the shape of the JSON sent back to the frontend.
- `RankedRestaurantResponse`: Extends the standard response to include AI-specific fields (`ai_rank` and `ai_explanation`).

### `crud.py` (Query Execution)
The `get_candidate_restaurants` function is responsible for the "First Pass" filtering. 
It queries the database using SQLAlchemy, applying filters for location (using `LIKE`), max budget (`<=`), and minimum rating (`>=`). It orders the results by rating and total votes, returning a maximum of **100** candidates. This ensures the AI is only fed high-quality, relevant data.

### `ai_service.py` (The AI Brain)
If the user inputs custom text into the "AI Preferences" box, this module takes over.
1. It takes the top 20 candidates from the DB and compresses their data (Name, Cuisine, Cost, Rating) into a tight JSON string to minimize token usage.
2. It constructs a highly engineered prompt instructing the Groq LLM to act as a harsh food critic, evaluating the 20 restaurants against the user's specific request.
3. The LLM is forced to output strict JSON containing the top 5 picks and a 1-sentence personalized explanation for why it was chosen.
4. The service parses the LLM JSON and returns a ranking map back to the main thread.

### `main.py` (The Orchestrator)
The FastAPI entry point. 
1. Resolves module paths (`sys.path.append`) to survive Railway's Nixpack build processes.
2. Initializes CORS middleware to allow the Vercel frontend to communicate with it.
3. Exposes the `POST /api/recommend` endpoint, joining the DB results from `crud.py` and the AI enrichment from `ai_service.py` into a unified JSON response. It includes fallback logic to return raw DB results if the AI service fails or times out.

---

## 5. Frontend Implementation Details
**Location:** `frontend/index.html`

The frontend is a masterclass in modern, lightweight web design.

### UI / UX Design
- **Glassmorphism:** The interface uses translucent panels (`bg-white/5`, `backdrop-blur-xl`) overlaid on a dark, radial-gradient background to create a premium, depth-rich feel.
- **Dynamic Scrollbars & Highlights:** Custom CSS ensures the scrollbars match the theme, and interactive elements hover and scale smoothly using Tailwind's `transition-all` utilities.

### Responsive Logic (Dual-Mode UX)
The app behaves differently based on screen size:
- **Desktop (`lg` screens):** Features a classic side-by-side layout. The search form remains locked on the left (`sticky`), while results scroll on the right.
- **Mobile (`<1024px`):** Functions as a **Single-Page Application (SPA)**. The form and results cannot fit on the screen together. The JavaScript dynamically hides the form (`search-view`) and shows the results (`results-view`) upon submission. A dedicated "← Back to Search" button is injected into the DOM, allowing users to toggle between screens instantly without reloading the webpage.

### API Networking
Axios is used to make the POST request. The script dynamically detects the environment:
```javascript
const isLocal = window.location.hostname === 'localhost';
const baseUrl = isLocal ? 'http://localhost:8000' : 'https://web-production-469b.up.railway.app';
```
This ensures developers can run the frontend locally and test against their local Python server without manually editing URLs, while the live Vercel site always points to Railway.

---

## 6. Deployment Architecture

### Railway (Backend)
Railway was chosen because it effortlessly handles Python/FastAPI deployments. 
- A `Procfile` is typically used, but Railway's Nixpacks builder automatically detects the `main:app` entry point.
- Environment variables (`GROQ_API_KEY`) are securely injected via the Railway dashboard.
- The `zomato.db` file is checked into Git (allowed via `.gitignore` exceptions), meaning the database is deployed statelessly alongside the code. 

### Vercel (Frontend)
Vercel was chosen to host the static HTML file on its Edge Network.
- The repository was connected, and the root directory was set to `frontend/`.
- Because it is pure HTML/JS, there is no build step (Framework preset: `Other`). Vercel simply serves the file to users instantly across the globe.

---

## 7. Future Enhancements & Maintainability
If another developer takes over this project, they should consider the following upgrades:
1. **PostgreSQL Migration:** While SQLite is excellent for this read-only Kaggle dataset, moving to PostgreSQL on Railway would allow for dynamic user reviews and real-time restaurant additions.
2. **Vector Search (RAG):** Instead of standard SQL filtering, we could embed the restaurant descriptions into a Vector Database (like Pinecone) to allow semantic searching (e.g., searching for "spicy food" without relying on the exact word "spicy" being in the cuisine list).
3. **Map Integration:** The frontend could be extended to use the Google Maps API or Leaflet.js to plot the recommended restaurants on a visual map based on their location tags.
