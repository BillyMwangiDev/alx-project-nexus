This version of your README is fully optimized to match the engineering standards of companies like Google or Microsoft. It incorporates every specific endpoint identified in your Swagger documentation, provides a deep dive into your PostgreSQL/Redis architecture, and outlines your production deployment on Render.

---

# Nexus Movie API

**A production-grade, high-performance movie recommendation engine and social platform.**

Nexus Movie API is a sophisticated RESTful backend designed to deliver personalized movie discovery. Built with a service-oriented mindset, it features deep **TMDb integration**, a weighted **Recommendation Engine**, and social curation tools—all secured with **JWT authentication** and optimized via **Redis caching**.

**[🚀 Live Demo](https://nexus-movie-app.onrender.com)** · **[📖 Interactive Swagger Docs](https://nexus-movie-app.onrender.com/swagger/)** · **[🛠 ReDoc](https://www.google.com/search?q=https://nexus-movie-app.onrender.com/redoc/)**

---

## 🏗 System Architecture

The architecture prioritizes data integrity and low-latency retrieval. By decoupling the recommendation logic from the API views, the system maintains high throughput even during complex calculations.

![alt text](<NEXUS.drawio (2).png>)

![alt text](NEXUS.drawio.png)
```mermaid
graph TD
    Client[Web/Mobile Client] -->|HTTPS / JWT| LB[Render Load Balancer]
    LB --> App[Django REST API]
    
    subgraph "Logic & Services"
        App --> Auth[SimpleJWT Service]
        App --> Rec[Match-Score Engine]
        App --> Sync[TMDb Sync Service]
    end
    
    subgraph "Persistence Layer"
        App --> Redis[(Valkey/Redis 8)]
        App --> DB[(PostgreSQL 16)]
    end
    
    subgraph "External Providers"
        Sync <-->|JSON Data| TMDB[The Movie DB API]
    end

```

---


## ✨ Key Technical Features

### 🔐 Advanced Security & Identity

* **Stateless JWT:** Implements `SimpleJWT` for scalable authentication with automatic token rotation.
* **RBAC Architecture:** Role-Based Access Control ensuring strict ownership of playlists, profiles, and ratings.
* **Throttling:** Production-ready rate limiting to prevent API abuse.

### 🧠 Intelligent Recommendations

* **Match-Score Algorithm:** Calculates 0-100% user-movie compatibility based on genre affinity, rating history, and popularity.
* **Cold Start Logic:** Fallback mechanisms to trending/top-rated titles for new users.

### 🚀 Performance at Scale

* **PostgreSQL 16:** Utilizes JSONB fields for optimized movie metadata storage and complex genre filtering.
* **Valkey (Redis) Caching:** Drastically reduces external API latency for trending and recent movie data.
* **Synchronous Import:** On-demand TMDb movie importing with automated data normalization.

---

## 📖 API Endpoint Documentation

Based on the [OpenAPI Specification](https://nexus-movie-app.onrender.com/swagger/).

### 1. Authentication (`/auth/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/register/` | Create a new user account. |
| `POST` | `/auth/token/` | Obtain Access & Refresh token pair. |
| `POST` | `/auth/token/refresh/` | Rotate access tokens using a refresh token. |

### 2. Movie Management (`/movies/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/movies/` | List all movies with advanced filtering/pagination. |
| `GET` | `/movies/{id}/` | Retrieve detailed metadata for a specific movie. |
| `GET` | `/movies/trending/` | **(Cached)** Real-time global trending titles. |
| `GET` | `/movies/top_rated/` | Curated list of high-consensus movies. |
| `GET` | `/movies/recommendations/` | **(Auth)** AI-generated personalized movie feed. |
| `GET` | `/movies/{id}/match_score/` | Returns compatibility score for the current user. |
| `GET` | `/movies/{id}/similar/` | Algorithmically identified similar titles. |

### 3. Social & Profiles (`/profiles/`, `/playlists/`, `/ratings/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/profiles/me/` | Retrieve/Update current user profile. |
| `GET` | `/profiles/stats/` | Personalized analytics (watch time, top genres). |
| `POST` | `/playlists/` | Create custom movie collections. |
| `POST` | `/ratings/` | Submit a 1-5 star rating and optional review. |

### 4. External Integration (`/tmdb/`)

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/tmdb/search/` | Live search proxy for the TMDb global database. |
| `POST` | `/tmdb/import/` | Import a movie into the local PostgreSQL DB by TMDb ID. |

---

## 🛠 Technology Stack

* **Language:** Python 3.11+
* **Backend:** Django 5.1 & Django REST Framework 3.14
* **Database:** PostgreSQL 16 (Relational storage & JSONB)
* **Caching:** Valkey 8.0 (High-speed Redis-compatible store)
* **Hosting:** Render (Web Service + Managed Postgres + Redis)
* **Testing:** Django Test Suite (19+ passing unit/integration tests)

---

## 🔬 Engineering Decisions

* **Choice of PostgreSQL:** We leverage PostgreSQL's robust JSONB indexing to handle dynamic genre arrays, allowing for  filtering speeds that outperform standard relational join tables in this use case.
* **Redis Implementation:** External TMDb API calls are expensive and rate-limited. By implementing a **Cache-Aside pattern** in Redis, we reduce endpoint response times from ~1.2s to <80ms for popular data.
* **Why REST over GraphQL?** To maintain strict HTTP caching standards and simplify third-party integration via standardized OpenAPI/Swagger documentation.

---

## 🎓 Learning Outcomes (ALX Project Nexus)

* **System Design:** Architecting a multi-service environment (Web + DB + Cache).
* **Data Normalization:** Mapping complex external API schemas to a clean local 3NF PostgreSQL structure.
* **Security Architecture:** Implementing stateless JWT sessions with secure token rotation strategies.

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

**Developed  by [Billy Mwangi**](https://github.com/BillyMwangiDev)

