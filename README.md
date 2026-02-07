A comprehensive backend API that delivers personalized movie recommendations with social features. Built with Django REST Framework, featuring TMDb integration, JWT authentication, and intelligent recommendation algorithms.

**Live Demo:** [https://nexus-movie-app.onrender.com](https://nexus-movie-app.onrender.com)
**API Documentation:** [https://nexus-movie-app.onrender.com/swagger/](https://nexus-movie-app.onrender.com/swagger/)

[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-19%20passing-brightgreen.svg)](.)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

##  Table of Contents

- [Project Overview](#project-overview)
- [Technical Stack](#technical-stack)
- [Features](#features)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Database Design](#database-design)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Challenges & Solutions](#challenges--solutions)

---

##  Project Overview

This repository demonstrates a **production-ready approach** to building RESTful APIs for a movie recommendation platform. The system integrates with **The Movie Database (TMDb) API** to provide real-time movie data while maintaining a local database for user-specific features like ratings, playlists, and personalized recommendations.

### Real-World Application

This project addresses real-world backend development challenges:
- **API Integration**: Seamless integration with third-party APIs (TMDb)
- **Performance**: Optimized database queries and efficient data handling
- **Security**: JWT-based authentication with proper authorization
- **User Experience**: Personalized recommendations based on user preferences
- **Scalability**: Designed to handle growing user base and data

### Learning Outcomes

Through this project, I gained practical experience with:
- RESTful API design and implementation
- Third-party API integration and data normalization
- Database design and normalization (1NF, 2NF, 3NF)
- JWT authentication and authorization
- Algorithm implementation (recommendation engine)
- Test-driven development
- API documentation with Swagger/OpenAPI

---

##  Technical Stack

| Technology | Purpose |
|------------|---------|
| **Django 5.0** | Web framework and ORM |
| **Django REST Framework 3.14** | RESTful API development |
| **PostgreSQL 16** | Primary relational database (Production) |
| **Valkey 8 (Redis)** | High-speed cache and task broker |
| **SimpleJWT** | JWT token authentication |
| **TMDb API** | External movie data source |
| **Swagger/OpenAPI** | Interactive API documentation |
| **Python 3.10+** | Primary programming language |

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS/JWT
┌──────▼─────────────────────────────┐
│      Django REST Framework          │
│  ┌─────────────────────────────┐  │
│  │   ViewSets & Serializers    │  │
│  └────────┬────────────────────┘  │
│           │                        │
│  ┌────────▼────────────────────┐  │
│  │   Business Logic Services   │  │
│  │   - TMDb Integration        │  │
│  │   - Recommendation Engine   │  │
│  └────────┬────────────────────┘  │
│           │                        │
│  ┌────────▼────────────────────┐  │
│  │   Data Models (ORM)         │  │
│  └────────┬────────────────────┘  │
└───────────┼──────────────────────────┘
            │
    ┌───────▼────────┐
    │  PostgreSQL    │
    │  / SQLite      │
    └────────────────┘
```

---

##  Features

### 1.  Movie Discovery
- **Browse Movies**: Paginated list of all movies with 20 items per page
- **Trending Movies**: Access to currently trending films
- **Top Rated**: Curated list of highest-rated movies (with 100+ votes)
- **Recent Additions**: Latest movies added to the database
- **Advanced Filtering**:
  - Filter by genre (Action, Sci-Fi, Drama, etc.)
  - Filter by year range (exact year, from year, to year)
  - Filter by rating (min/max vote average)
  - Filter by runtime (min/max duration in minutes)
- **Full-Text Search**: Search movies by title and overview
- **Sorting**: Sort by popularity, rating, release date, or recency

### 2.  User Authentication
- **User Registration**: Create new accounts with email validation
- **JWT Authentication**: Secure token-based authentication
- **Token Refresh**: Seamless session management with refresh tokens
- **Protected Endpoints**: Secure access to user-specific features
- **Rate Limiting**: 100 requests/hour for anonymous users, 1000 requests/hour for authenticated users

### 3.  Rating System
- **Rate Movies**: 1-5 star ratings with optional text reviews
- **View Ratings**: See all your ratings with movie details
- **Update Ratings**: Modify your previous ratings
- **Delete Ratings**: Remove ratings you no longer want
- **Unique Constraint**: One rating per user per movie
- **My Ratings Endpoint**: Dedicated endpoint for user's rating history

### 4.  Playlist Management
- **Create Playlists**: Curate custom movie collections
- **Public/Private Visibility**: Control who can see your playlists
- **Add/Remove Movies**: Flexible playlist management
- **Playlist Discovery**: Browse public playlists from other users
- **Movie Count**: Track number of movies in each playlist
- **My Playlists**: Quick access to your own collections

### 5.  Personalized Recommendations
- **Match Score Algorithm**: Intelligent scoring system (0-100) based on:
  - **40%** - Match with user's favorite genres
  - **30%** - Similarity to highly-rated movies in history
  - **20%** - Movie's overall rating quality
  - **10%** - Current popularity metrics
- **Smart Filtering**: Automatically excludes already-rated movies
- **Customizable Limit**: Request specific number of recommendations
- **Profile-Based**: Updates dynamically with user preferences

### 6.  User Profile Management
- **View Profile**: Access profile information and preferences
- **Update Preferences**: Set favorite genres for better recommendations
- **User Statistics**: Comprehensive viewing analytics:
  - Total movies rated
  - Average rating score
  - Favorite genres (based on high ratings)
  - Total watch time in hours
  - Highest and lowest rated movies

### 7.  TMDb Integration
- **Live Search**: Search TMDb database directly from the API
- **Import Movies**: Bring any TMDb movie into your local database
- **Automatic Sync**: Background commands to sync popular/trending movies
- **Data Normalization**: TMDb data converted to local schema format
- **Management Commands**:
  - `sync_tmdb_movies`: Batch import movies (popular, trending, top_rated)
  - `search_tmdb`: Search and optionally save movies
  - `test_tmdb_config`: Verify API connection

### 8.  Similar Movies
- **Genre-Based Recommendations**: Find movies with overlapping genres
- **Relevance Sorting**: Ordered by genre overlap and rating
- **Configurable Results**: Set limit on number of similar movies

### 9.  Interactive API Documentation
- **Swagger UI**: Full interactive documentation at root URL
- **ReDoc**: Alternative documentation view
- **Try It Out**: Test endpoints directly from browser
- **Schema Export**: OpenAPI 3.0 specification available
- **Request Examples**: Pre-filled examples for all endpoints

### 10.  Admin Panel
- **Django Admin**: Full-featured management interface
- **User Management**: Manage users and profiles
- **Movie Catalog**: Browse and edit movie database
- **Rating Moderation**: View and manage user ratings
- **Playlist Management**: Oversee user playlists
- **Advanced Filtering**: Filter and search across all models
- **Inline Editing**: Edit related objects without navigation

### 11.  Asynchronous Processing (Celery & Redis)
- **Background Tasks**: Offload heavy operations to Celery workers.
- **Task Scheduling**: Periodic sync of movie data using Celery Beat.
- **Valkey Broker**: High-speed task queuing via Render's Key-Value service.

### 12.  DevOps & Infrastructure
- **Docker Ready**: Containerized environment with `docker-compose` for unified development.
- **Continuous Integration**: Automated testing and linting via GitHub Actions.
- **Automated Deployment**: CI/CD pipeline integrated with Render for seamless updates.
- **Regional Optimization**: Deployed in `frankfurt` for lower latency.
- **Auto-Provisioning**: Deployment scripts wait for infrastructure ready-states.

---

##  Getting Started

### Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation) package manager
- Git
- TMDb API Key ([Get free key](https://www.themoviedb.org/settings/api))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/nexus-movie-api.git
cd nexus-movie-api/Movie-Recommendation-BE

# 2. Install dependencies
poetry install

# 3. Activate virtual environment
poetry shell

# 4. Configure environment
# Edit config/settings.py and add:
TMDB_API_KEY = 'your_api_key_here'

# 5. Run migrations
poetry run python manage.py migrate

# 6. Create superuser
poetry run python manage.py createsuperuser

# 7. Load sample data
python manage.py populate_movies

# OR sync from TMDb (100 popular movies)
python manage.py sync_tmdb_movies --category popular --pages 5

# 8. Start development server
poetry run python manage.py runserver
```

### Quick Test

```bash
# Test TMDb connection
python manage.py test_tmdb_config

# Search for a movie
python manage.py search_tmdb "Inception" --save

# Run tests
python manage.py test
```

Visit [https://nexus-movie-app.onrender.com/swagger/](https://nexus-movie-app.onrender.com/swagger/) to see the interactive API documentation!

---

## 📚 API Documentation

### Base URL
```
http://127.0.0.1:8000/api/
```

### Authentication Endpoints

```http
POST /api/auth/register/          # Register new user
POST /api/auth/token/             # Get access & refresh tokens
POST /api/auth/token/refresh/     # Refresh access token
```

### Movie Endpoints

```http
GET  /api/movies/                     # List movies (paginated)
GET  /api/movies/{id}/                # Movie details
GET  /api/movies/trending/            # Trending movies
GET  /api/movies/top_rated/           # Top rated movies
GET  /api/movies/recent/              # Recently added
GET  /api/movies/recommendations/     # Personalized (auth required)
GET  /api/movies/{id}/similar/        # Similar movies
GET  /api/movies/{id}/match_score/    # Match score (auth required)
```

**Query Parameters:**
- `search` - Search in title/overview
- `genre` - Filter by genre name
- `year` - Exact year
- `year_gte` - From year
- `year_lte` - To year
- `min_rating` - Minimum vote average
- `max_rating` - Maximum vote average
- `min_runtime` - Minimum duration (minutes)
- `max_runtime` - Maximum duration (minutes)
- `ordering` - Sort by field (use `-` for descending)

**Examples:**
```http
GET /api/movies/?genre=Action&min_rating=7.5
GET /api/movies/?year_gte=2020&ordering=-vote_average
GET /api/movies/?search=dark knight
```

### Rating Endpoints

```http
GET    /api/ratings/               # List ratings
POST   /api/ratings/               # Create rating (auth required)
GET    /api/ratings/my_ratings/    # My ratings (auth required)
GET    /api/ratings/{id}/          # Rating details
PUT    /api/ratings/{id}/          # Update rating (owner only)
PATCH  /api/ratings/{id}/          # Partial update (owner only)
DELETE /api/ratings/{id}/          # Delete rating (owner only)
```

### Playlist Endpoints

```http
GET    /api/playlists/                     # List public playlists
POST   /api/playlists/                     # Create playlist (auth required)
GET    /api/playlists/my_playlists/        # My playlists (auth required)
GET    /api/playlists/{id}/                # Playlist details
PUT    /api/playlists/{id}/                # Update playlist (owner only)
PATCH  /api/playlists/{id}/                # Partial update (owner only)
DELETE /api/playlists/{id}/                # Delete playlist (owner only)
POST   /api/playlists/{id}/add_movie/      # Add movie (owner only)
POST   /api/playlists/{id}/remove_movie/   # Remove movie (owner only)
```

### Profile Endpoints

```http
GET   /api/profiles/me/      # Get my profile (auth required)
PUT   /api/profiles/me/      # Update profile (auth required)
PATCH /api/profiles/me/      # Partial update (auth required)
GET   /api/profiles/stats/   # Get statistics (auth required)
```

### TMDb Integration Endpoints

```http
GET  /api/tmdb/search/?q={query}   # Search TMDb directly
POST /api/tmdb/import/             # Import movie by tmdb_id (auth required)
```

For detailed API documentation with request/response examples, visit the interactive Swagger UI at [https://nexus-movie-app.onrender.com/swagger/](https://nexus-movie-app.onrender.com/swagger/)

---

##  Database Design

### Entity Relationship Diagram

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ 1:1
       │
┌──────▼────────────┐
│   UserProfile     │
└───────────────────┘

┌─────────────┐           ┌──────────────────┐
│    User     │───────┐   │  MovieMetadata   │
└─────────────┘    1:N│   └──────────────────┘
                      │            │
                 ┌────▼──────┐    │N:M
                 │  Rating   │    │
                 └───────────┘    │
                                  │
┌─────────────┐           ┌──────▼──────────┐
│    User     │───────────│   Playlist      │
└─────────────┘   1:N     └─────────────────┘
```

### Tables

**1. auth_user** (Django built-in)
- User authentication and basic info

**2. movies_api_userprofile**
- Extended user data (favorite_genres, bio, avatar_url)

**3. movies_api_moviemetadata**
- Cached movie data from TMDb
- Fields: tmdb_id, title, overview, release_date, poster_path, vote_average, popularity, genres (JSON), runtime

**4. movies_api_rating**
- User ratings for movies
- Unique constraint: (user, movie)
- Fields: score (1-5), review, created_at

**5. movies_api_playlist**
- User-created movie collections
- Fields: name, description, visibility (public/private)

**6. movies_api_playlist_movies**
- Junction table for Playlist ↔ MovieMetadata (Many-to-Many)

### Normalization

The database is fully normalized:
- **1NF**: All columns contain atomic values
- **2NF**: No partial dependencies (all non-key attributes depend on entire primary key)
- **3NF**: No transitive dependencies (non-key attributes don't depend on other non-key attributes)

For complete database documentation, see [DATABASE.md](DATABASE.md)

---

##  Testing

### Test Suite

```bash
# Run all tests
python manage.py test

# Run with verbose output
python manage.py test --verbosity=2

# Run specific test class
python manage.py test apps.movies_api.tests.MovieMetadataTestCase
```

### Test Coverage

**19 passing tests** covering:

-  **Model Tests** (7 tests)
  - Movie creation and validation
  - User profile auto-creation
  - Rating constraints
  - Playlist functionality

-  **API Endpoint Tests** (7 tests)
  - Movie list and detail endpoints
  - Authentication requirements
  - Rating creation with auth
  - User registration

-  **Recommendation Tests** (2 tests)
  - Match score calculation
  - Recommendations generation

-  **Integration Tests** (3 tests)
  - End-to-end workflows
  - Permission checks

```
Found 19 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...................
----------------------------------------------------------------------
Ran 19 tests in 17.865s

OK
Destroying test database for alias 'default'...
```

---

##  Project Structure

```
Movie-Recommendation-BE/
├── apps/
│   └── movies_api/
│       ├── management/
│       │   └── commands/
│       │       ├── __init__.py
│       │       ├── populate_movies.py      # Sample data loader
│       │       ├── sync_tmdb_movies.py     # TMDb bulk sync
│       │       ├── search_tmdb.py          # TMDb search CLI
│       │       └── test_tmdb_config.py     # TMDb connection test
│       ├── services/
│       │   ├── __init__.py
│       │   ├── tmdb_service.py            # TMDb API integration
│       │   └── recommendation_service.py   # Recommendation engine
│       ├── __init__.py
│       ├── admin.py                       # Admin interface config
│       ├── apps.py                        # App configuration
│       ├── filters.py                     # Custom query filters
│       ├── models.py                      # Database models
│       ├── serializers.py                 # DRF serializers
│       ├── signals.py                     # Django signals
│       ├── tests.py                       # Test suite
│       ├── urls.py                        # URL routing
│       └── views.py                       # API views
├── config/
│   ├── __init__.py
│   ├── settings.py                        # Django settings
│   ├── urls.py                            # Main URL config
│   └── wsgi.py                            # WSGI configuration
├── .env.example                           # Environment template
├── .gitignore                             # Git ignore rules
├── db.sqlite3                             # SQLite database
├── manage.py                              # Django CLI
├── requirements.txt                       # Python dependencies
└── README.md                              # This file
```

---

##  Challenges & Solutions

### Challenge 1: JSONField Filtering in SQLite

**Problem**: SQLite doesn't support `contains` lookup on JSON fields, causing errors when filtering by genre.

**Solution**: 
```python
def filter_by_genre(self, queryset, name, value):
    if connection.vendor == 'sqlite':
        # Filter in Python for SQLite
        movie_ids = [m.id for m in queryset if m.genres and value in m.genres]
        return queryset.filter(id__in=movie_ids)
    else:
        # Use native JSON query for PostgreSQL
        return queryset.filter(genres__contains=[value])
```

### Challenge 2: TMDb Data Normalization

**Problem**: TMDb API returns data in different formats than our database schema.

**Solution**: Created a `normalize_movie_data()` service method that:
- Converts TMDb format to our model fields
- Handles missing/null values gracefully
- Parses dates and extracts genre names
- Maps TMDb IDs to local database IDs

### Challenge 3: Recommendation Algorithm

**Problem**: Calculating personalized match scores efficiently without over-complicating.

**Solution**: Implemented weighted scoring system:
- Genre matching (40%)
- Rating history analysis (30%)
- Movie quality (20%)
- Popularity (10%)

Keeps algorithm simple yet effective while being easy to tune and improve.

### Challenge 4: Authentication in Swagger UI

**Problem**: Users confused about proper JWT token format.

**Solution**:
- Clear documentation in Swagger
- Authorization button prominently displayed
- Format: `Bearer {token}` (no quotes)
- Helpful error messages

---

## 🎓 Learning Outcomes

### Technical Skills Gained

1. **RESTful API Design**
   - Proper HTTP method usage
   - Resource-based URL structure
   - Pagination and filtering
   - Error handling patterns

2. **Django & DRF Mastery**
   - ViewSets and Serializers
   - Custom permissions
   - Signals for automation
   - ORM optimization

3. **Database Design**
   - Normalization principles
   - Relationship modeling
   - Index optimization
   - Constraint implementation

4. **Third-Party Integration**
   - API key management
   - Rate limiting respect
   - Data transformation
   - Error recovery

5. **Authentication & Security**
   - JWT implementation
   - Token refresh flow
   - Permission-based access
   - Input validation

6. **Algorithm Implementation**
   - Recommendation logic
   - Scoring systems
   - Data filtering
   - Performance optimization

7. **Testing**
   - Unit test creation
   - API endpoint testing
   - Test fixtures
   - Assertion techniques

### Best Practices Applied

- **Service Layer Pattern**: Business logic separated from views
- **DRY Principle**: Reusable serializers and filters
- **Single Responsibility**: Each model, view, service has one job
- **Documentation**: Code comments and API docs maintained
- **Error Handling**: Graceful failures with helpful messages
- **Security First**: Authentication, authorization, validation throughout

---

##  License

This project is licensed under the MIT License.

---

##  Acknowledgments

- **The Movie Database (TMDb)** - For providing comprehensive movie data via their free API
- **Django & DRF Communities** - For excellent documentation and support
- **ALX ProDev Backend Engineering Program** - For the project requirements and learning structure

---

##  Contact

**GitHub**: [BillyMwangiDev](https://github.com/BillyMwangiDev)  
**Email**: [Contact through GitHub]
**LinkedIn**: [Billy Mwangi](https://www.linkedin.com/in/billymwangi/)

---

##  Future Enhancements

Features planned for future versions:

- [x] **Redis Caching**: Implement Redis for search results and trending data (Implemented via Valkey 8)
- [x] **Celery Background Tasks**: Add async processing for bulk operations
- [ ] **GraphQL API**: Alternative query language for flexible data fetching
- [x] **Docker**: Containerize application for easier deployment
- [x] **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions
- [ ] **WebSocket Support**: Real-time notifications for new ratings/playlists
- [ ] **Social Features**: User following and activity feeds
- [ ] **Advanced Analytics**: Viewing trends and recommendation insights
- [ ] **Movie Trailers**: Integrate YouTube API for trailers
- [ ] **Email Notifications**: Rating reminders and playlist updates
- [ ] **Export/Import**: Backup playlists as JSON/CSV
- [ ] **Multi-language Support**: i18n for global audience

---



*Built with passion for movies and clean code* 🎬