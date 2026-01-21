# Nexus Movie API - Database Schema Documentation

## Table of Contents

1. [Components](#components)
2. [Entities](#entities)
3. [Attributes](#attributes)
4. [Relationships](#relationships)
5. [Normalization](#normalization)

---

## Components

### System Architecture Components

*Core Modules:*

* Authentication & Authorization Module
* Movie Discovery Module
* Social Interaction Module
* Personalization Module
* External API Integration Module

*Data Storage Components:*

* Primary Database: PostgreSQL (relational data)
* Cache Layer: Redis (search results, trending data)
* Task Queue: Celery + RabbitMQ (background processing)

*Data Flow:*

1. External TMDb API → Background Sync → Local Movie Cache
2. User Actions → Django ORM → PostgreSQL
3. Frequent Queries → Redis Cache → Fast Response
4. Background Tasks → Celery Workers → Database Updates

---

## Entities

### Primary Entities

#### 1. User

*Description:* Registered system users who interact with the platform
*Type:* Strong Entity
*Primary Key:* id (auto-generated integer)
*Purpose:* Handles authentication and serves as the parent entity for all user-related data

#### 2. UserProfile

*Description:* Extended user information for personalization
*Type:* Weak Entity (depends on User)
*Primary Key:* id (auto-generated integer)
*Foreign Key:* user_id (references User)
*Purpose:* Stores preferences and settings for personalized recommendations

#### 3. MovieMetadata

*Description:* Cached movie information from TMDb API
*Type:* Strong Entity
*Primary Key:* id (auto-generated integer)
*Alternate Key:* tmdb_id (unique external identifier)
*Purpose:* Local cache to minimize external API calls and enable relational queries

#### 4. Rating

*Description:* User ratings and reviews for movies
*Type:* Weak Entity (depends on both User and MovieMetadata)
*Primary Key:* id (auto-generated integer)
*Foreign Keys:* user_id, movie_id
*Purpose:* Captures user opinions and powers personalization algorithms

#### 5. Playlist

*Description:* User-created movie collections
*Type:* Weak Entity (depends on User)
*Primary Key:* id (auto-generated integer)
*Foreign Key:* owner_id (references User)
*Purpose:* Social feature allowing users to curate and share movie lists

#### 6. PlaylistMovies (Junction Entity)

*Description:* Association between playlists and movies
*Type:* Junction / Associative Entity
*Primary Key:* id (auto-generated integer)
*Foreign Keys:* playlist_id, moviemetadata_id
*Purpose:* Implements many-to-many relationship between Playlist and MovieMetadata

---

## Attributes

### Entity: User (auth_user)

| Attribute    | Data Type    | Constraints                  | Description            |
| ------------ | ------------ | ---------------------------- | ---------------------- |
| id           | INTEGER      | PK, NOT NULL, AUTO_INCREMENT | Unique identifier      |
| username     | VARCHAR(150) | UNIQUE, NOT NULL             | Login username         |
| email        | VARCHAR(254) | UNIQUE                       | Email address          |
| password     | VARCHAR(128) | NOT NULL                     | Hashed password        |
| first_name   | VARCHAR(150) | NULLABLE                     | First name             |
| last_name    | VARCHAR(150) | NULLABLE                     | Last name              |
| is_staff     | BOOLEAN      | DEFAULT FALSE                | Admin privileges flag  |
| is_active    | BOOLEAN      | DEFAULT TRUE                 | Account status         |
| is_superuser | BOOLEAN      | DEFAULT FALSE                | Superuser flag         |
| date_joined  | DATETIME     | NOT NULL                     | Registration timestamp |
| last_login   | DATETIME     | NULLABLE                     | Last login timestamp   |

*Derived Attributes:*

* full_name (computed from first_name + last_name)
* account_age (computed from date_joined to current date)

---

### Entity: UserProfile (movies_api_userprofile)

| Attribute       | Data Type    | Constraints                  | Description                 |
| --------------- | ------------ | ---------------------------- | --------------------------- |
| id              | INTEGER      | PK, NOT NULL, AUTO_INCREMENT | Unique identifier           |
| user_id         | INTEGER      | FK, UNIQUE, NOT NULL         | References User.id          |
| favorite_genres | JSON         | DEFAULT '[]'                 | List of preferred genres    |
| bio             | TEXT         | MAX 500 chars                | User biography              |
| avatar_url      | VARCHAR(200) | NULLABLE                     | Profile picture URL         |
| created_at      | DATETIME     | NOT NULL                     | Profile creation timestamp  |
| updated_at      | DATETIME     | NOT NULL                     | Last modification timestamp |

*Multi-valued Attribute:*

* favorite_genres (stored as JSON array)

*Derived Attributes:*

* profile_completeness (percentage based on filled fields)

---

### Entity: MovieMetadata (movies_api_moviemetadata)

| Attribute     | Data Type    | Constraints                  | Description              |
| ------------- | ------------ | ---------------------------- | ------------------------ |
| id            | INTEGER      | PK, NOT NULL, AUTO_INCREMENT | Unique identifier        |
| tmdb_id       | INTEGER      | UNIQUE, NOT NULL             | TMDb API identifier      |
| title         | VARCHAR(255) | NOT NULL                     | Movie title              |
| overview      | TEXT         | NULLABLE                     | Plot summary             |
| release_date  | DATE         | NULLABLE                     | Release date             |
| poster_path   | VARCHAR(255) | NULLABLE                     | Poster image path        |
| backdrop_path | VARCHAR(255) | NULLABLE                     | Backdrop image path      |
| vote_average  | FLOAT        | DEFAULT 0.0                  | TMDb average rating      |
| vote_count    | INTEGER      | DEFAULT 0                    | Number of TMDb votes     |
| popularity    | FLOAT        | DEFAULT 0.0                  | TMDb popularity score    |
| genres        | JSON         | DEFAULT '[]'                 | List of genre names      |
| runtime       | INTEGER      | NULLABLE                     | Duration in minutes      |
| created_at    | DATETIME     | NOT NULL                     | Cache creation timestamp |
| updated_at    | DATETIME     | NOT NULL                     | Last sync timestamp      |

*Multi-valued Attributes:*

* genres (stored as JSON array)

*Derived Attributes:*

* poster_url (base_url + poster_path)
* backdrop_url (base_url + backdrop_path)
* release_year (derived from release_date)
* cache_age (computed from created_at to current date)

---

### Entity: Rating (movies_api_rating)

| Attribute  | Data Type | Constraints                  | Description                 |
| ---------- | --------- | ---------------------------- | --------------------------- |
| id         | INTEGER   | PK, NOT NULL, AUTO_INCREMENT | Unique identifier           |
| user_id    | INTEGER   | FK, NOT NULL                 | References User.id          |
| movie_id   | INTEGER   | FK, NOT NULL                 | References MovieMetadata.id |
| score      | INTEGER   | CHECK (1-5), NOT NULL        | Rating value                |
| review     | TEXT      | MAX 1000 chars               | Optional text review        |
| created_at | DATETIME  | NOT NULL                     | Rating creation timestamp   |
| updated_at | DATETIME  | NOT NULL                     | Last edit timestamp         |

*Composite Key:*

* (user_id, movie_id)

*Derived Attributes:*

* is_positive (score >= 4)
* age_of_rating (computed from created_at to current date)

---

### Entity: Playlist (movies_api_playlist)

| Attribute   | Data Type    | Constraints                              | Description                 |
| ----------- | ------------ | ---------------------------------------- | --------------------------- |
| id          | INTEGER      | PK, NOT NULL, AUTO_INCREMENT             | Unique identifier           |
| owner_id    | INTEGER      | FK, NOT NULL                             | References User.id          |
| name        | VARCHAR(200) | NOT NULL                                 | Playlist name               |
| description | TEXT         | MAX 500 chars                            | Playlist description        |
| visibility  | VARCHAR(10)  | CHECK (public, private), DEFAULT private | Access level                |
| created_at  | DATETIME     | NOT NULL                                 | Creation timestamp          |
| updated_at  | DATETIME     | NOT NULL                                 | Last modification timestamp |

*Derived Attributes:*

* movie_count
* is_public
* age_of_playlist

---

### Entity: PlaylistMovies (movies_api_playlist_movies)

| Attribute        | Data Type | Constraints                  | Description                 |
| ---------------- | --------- | ---------------------------- | --------------------------- |
| id               | INTEGER   | PK, NOT NULL, AUTO_INCREMENT | Unique identifier           |
| playlist_id      | INTEGER   | FK, NOT NULL                 | References Playlist.id      |
| moviemetadata_id | INTEGER   | FK, NOT NULL                 | References MovieMetadata.id |

*Composite Key:*

* (playlist_id, moviemetadata_id)

---

## Relationships

### User to UserProfile (One-to-One)

* Relationship Type: One-to-One
* User participation: Optional
* UserProfile participation: Mandatory
* Cardinality: (1,1) to (0,1)

*Implementation:*

* UserProfile.user_id is UNIQUE
* ON DELETE CASCADE

*Business Rules:*

* One user has at most one profile
* A profile cannot exist without a user

---

### User to Rating (One-to-Many)

* Relationship Type: One-to-Many
* User participation: Optional
* Rating participation: Mandatory

*Implementation:*

* Rating.user_id as foreign key
* ON DELETE CASCADE

---

### User to Playlist (One-to-Many)

* Relationship Type: One-to-Many
* Playlist must have an owner
* ON DELETE CASCADE

---

### MovieMetadata to Rating (One-to-Many)

* One movie can have many ratings
* Each rating belongs to one movie
* Unique constraint on (user_id, movie_id)

---

### MovieMetadata to Playlist (Many-to-Many)

* Implemented via PlaylistMovies
* Unique constraint on (playlist_id, moviemetadata_id)
* ON DELETE CASCADE

---

## Normalization

### First Normal Form (1NF)

* Atomic attributes enforced across tables
* JSON fields used intentionally for flexibility

### Second Normal Form (2NF)

* No partial dependencies
* All non-key attributes depend on full primary keys

### Third Normal Form (3NF)

* No transitive dependencies
* Derived values are computed, not stored

---

### Normalization Summary

| Normal Form | Status    | Notes                      |
| ----------- | --------- | -------------------------- |
| 1NF         | Compliant | JSON fields justified      |
| 2NF         | Compliant | No partial dependencies    |
| 3NF         | Compliant | No transitive dependencies |

---

### Denormalization Decisions

* JSON fields for genres and preferences to reduce joins
* Cached TMDb data for performance
* Timestamps for auditing and recency queries

---

### Benefits

* Strong data integrity
* Clear maintainability
* Optimized performance
* Scalable schema design
