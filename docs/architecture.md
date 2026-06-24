# Comprehensive Architecture: AI-Powered Restaurant Recommendation System

## 1. Executive Summary
This document outlines the detailed system architecture, component design, and data flows for an AI-Powered Restaurant Recommendation System. Inspired by Zomato, the platform dynamically matches users with restaurants by combining deterministic dataset filtering with non-deterministic, context-aware reasoning powered by a Large Language Model (LLM).

---

## 2. System Context Diagram
This diagram illustrates the high-level interactions between the system and external entities.

```mermaid
graph TD
    User([User]) -->|Inputs Preferences & Constraints| System[Restaurant Recommendation System]
    System -->|Returns Tailored Recommendations| User
    
    System -.->|Fetches Restaurant Dataset| HF[(Hugging Face Hub)]
    System -.->|Sends Prompt & Context| LLM[LLM Provider API <br/> Groq]
    LLM -.->|Returns Reasoning & Rankings| System
```

---

## 3. High-Level Container Architecture
The architecture follows a modern decoupled approach with a distinct Frontend, Backend API, Database, and an LLM orchestration layer.

```mermaid
graph TD
    subgraph Frontend Client
        UI[Web/Mobile Interface]
        State[State Management]
    end

    subgraph Backend API Services
        API[API Gateway / Router]
        PrefValidator[Preference Validator]
        RecEngine[Recommendation Orchestrator]
        PromptBuilder[Prompt Builder]
    end

    subgraph Data Persistence
        DB[(Primary Database<br/>PostgreSQL/MongoDB)]
        Cache[(Redis Cache)]
    end

    subgraph Data Pipeline
        Ingest[Dataset Downloader]
        ETL[Data Cleaning & ETL]
    end

    subgraph External AI Layer
        LLM[Large Language Model]
    end

    %% Connections
    UI <-->|JSON over REST/GraphQL| API
    API --> PrefValidator
    PrefValidator --> RecEngine
    
    Ingest -->|Raw Data| ETL
    ETL -->|Structured Data| DB
    
    RecEngine <-->|Query Structured Data| DB
    RecEngine <-->|Cache Repeated Queries| Cache
    RecEngine --> PromptBuilder
    PromptBuilder -->|Context-Rich Prompt| LLM
    LLM -->|Parsed Output| RecEngine
```

---

## 4. Detailed Component Breakdown

### 4.1. Data Pipeline (Offline Phase)
- **Dataset Downloader:** Connects to the Hugging Face API (`ManikaSaini/zomato-restaurant-recommendation`) and pulls the raw data.
- **ETL Engine (Extract, Transform, Load):** 
  - *Cleaning*: Handles missing values, normalizes cost and rating scales.
  - *Geospatial Data*: Converts location strings into standardized representations.
  - *Categorization*: Standardizes cuisines and tags (e.g., "fast-food", "fine-dining").
- **Database:** Stores the cleaned data. A SQL database (PostgreSQL) is ideal here to allow complex querying like `WHERE location = 'X' AND cost < Y`.

### 4.2. Backend API & Integration Layer (Online Phase)
- **API Gateway:** Exposes endpoints like `POST /api/recommendations`.
- **Preference Validator:** Ensures user inputs are safe and correctly formatted.
- **Query Engine:** Transforms the user's hard constraints (Location, Budget, Minimum Rating, Specific Cuisine) into strict SQL/NoSQL queries. **Crucial Step:** This prevents sending 10,000+ restaurants to the LLM, reducing it to a candidate pool of ~20-50 highly relevant restaurants.
- **Prompt Builder:** Takes the candidate pool and injects it into a templated LLM prompt alongside the user's "soft" constraints (e.g., "looking for a quiet place for an anniversary", "good for toddlers").

### 4.3. Recommendation Engine (LLM Layer)
- **LLM Provider:** Evaluates the candidate pool against the soft constraints. 
- **Response Parser:** The LLM is instructed to output structured JSON. The parser validates the JSON, ensuring the LLM provided valid rankings and explanations for the selected top matches.

---

## 5. Architectural Flows (Sequence Diagrams)

### 5.1. Data Ingestion Flow (Asynchronous / Scheduled)
```mermaid
sequenceDiagram
    participant Cron as Scheduler
    participant Pipeline as ETL Pipeline
    participant HF as Hugging Face Hub
    participant DB as Database

    Cron->>Pipeline: Trigger Ingestion (Weekly/Monthly)
    Pipeline->>HF: Request Dataset update
    HF-->>Pipeline: Return CSV/JSON Data
    Pipeline->>Pipeline: Clean & Normalize Data
    Pipeline->>Pipeline: Extract Cost, Rating, Cuisine
    Pipeline->>DB: Bulk Upsert/Insert Records
    DB-->>Pipeline: Acknowledge Success
```

### 5.2. Recommendation Generation Flow (Synchronous)
```mermaid
sequenceDiagram
    participant User
    participant UI as Frontend App
    participant API as Backend (FastAPI/Node)
    participant DB as Database
    participant LLM as LLM API

    User->>UI: Enter preferences (Delhi, High Budget, Italian, "Romantic")
    UI->>API: POST /api/recommend
    
    API->>API: Validate input parameters
    API->>DB: Query: loc=Delhi, budget=High, cuisine=Italian
    DB-->>API: Return Top 30 candidate restaurants
    
    API->>API: Format candidates into Prompt String
    API->>LLM: POST Prompt + Context ("Find romantic spots from this list...")
    
    LLM-->>API: Return Top 5 Ranked with Explanations (JSON)
    
    API->>API: Parse & format response
    API-->>UI: Return JSON Array (Ranked List)
    
    UI-->>User: Render beautiful recommendation cards
```

---

## 6. Data Schema

### 6.1. Restaurant Entity (Database)
```json
{
  "restaurant_id": "string (UUID)",
  "name": "string",
  "location": {
    "city": "string",
    "neighborhood": "string"
  },
  "cuisine_tags": ["string"],
  "average_cost_for_two": "integer",
  "rating": "float",
  "votes": "integer",
  "metadata": {
    "has_online_delivery": "boolean",
    "has_table_booking": "boolean"
  }
}
```

### 6.2. LLM Output Structure (Expected)
```json
{
  "recommendations": [
    {
      "restaurant_id": "string",
      "rank": 1,
      "ai_explanation": "Perfect for a romantic evening due to its quiet ambiance and highly-rated Italian wine selection. It perfectly matches your high budget."
    }
  ]
}
```

---

## 7. Scalability & Performance Considerations
1. **Caching (Redis):** If multiple users query exactly "Delhi, Italian, Medium Budget, Family Friendly" in a short timeframe, the LLM response can be cached to save API costs and reduce latency from 3-5 seconds to <100ms.
2. **Context Window Limits:** The Backend must forcefully limit the candidate pool size (e.g., Top 20) before sending data to the LLM to prevent context overflow and reduce token consumption.
3. **Structured Generation:** Using tools like LangChain or Groq's JSON mode/structured outputs ensures the LLM returns parsable data instead of raw text, preventing frontend breaking errors.
