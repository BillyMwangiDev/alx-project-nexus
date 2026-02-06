# Production Deployment Guide

This guide walks through deploying the ALX Project Nexus Movie Recommendation API to Render with full CI/CD automation via GitHub Actions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [GitHub Setup](#github-setup)
3. [Render Setup](#render-setup)
4. [Environment Variables](#environment-variables)
5. [Deployment Process](#deployment-process)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Monitoring & Rollback](#monitoring--rollback)

---

## Prerequisites

### Required Accounts
- **GitHub**: Repository with admin access
- **Render**: Production deployment platform (free or paid plan)
- **TMDb API**: Valid API key for movie data
- **Docker** (optional): For local testing of containerized setup

### Required Knowledge
- Git basics (push, pull, branching)
- Environment variables and secrets management
- Basic Django/Python debugging

---

## GitHub Setup

### Step 1: Create Required Secrets

GitHub Secrets are encrypted environment variables used by CI/CD pipeline. Navigate to your repository:

```
Settings → Secrets and variables → Actions → New repository secret
```

#### Secret 1: `TMDB_API_KEY`
- **Value**: Your TMDb API key (v3 Authentication)
- **Get it**: https://www.themoviedb.org/settings/api
- **Format**: `abc123def456...` (no quotes)

```bash
# Example (don't commit to repo):
TMDB_API_KEY=eyJhbGciOiJIUzI1NiJ9...
```

#### Secret 2: `SECRET_KEY`
- **Value**: Django SECRET_KEY for production
- **Generate it**:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- **Note**: Keep this safe! Store in password manager

```bash
# Example (generate fresh):
SECRET_KEY=django-insecure-ab#c@d%efgh^ijklmn&opqrst*uvwxyz
```

#### Secret 3: `RENDER_DEPLOY_HOOK_URL`
- **Value**: Render deployment webhook URL
- **Purpose**: Triggers automatic deployment after tests pass
- **Get it**: (See [Render Setup](#render-setup) below)

**Add all three secrets to GitHub Actions:**

| Secret Name | Source |
|---|---|
| `TMDB_API_KEY` | TMDb account settings |
| `SECRET_KEY` | Run Django key generation command |
| `RENDER_DEPLOY_HOOK_URL` | Render dashboard (generated later) |

---

## Render Setup

### Step 1: Create PostgreSQL Database

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `nexus-postgres`
   - **Database**: `nexus_db`
   - **User**: `nexus_user`
   - **Region**: Same as your API (e.g., `us-east`)
   - **Plan**: `Free` (0 credits/month) or `Standard` ($12+/month)
4. **Create Database**
5. Copy the **Internal Database URL** (format: `postgresql://user:pass@host/db`)

### Step 2: Create Redis Cache

1. Click **New** → **Redis**
2. Configure:
   - **Name**: `nexus-redis`
   - **Region**: Same as PostgreSQL
   - **Plan**: `Free` (limited) or `Starter` ($5+/month)
3. **Create Redis**
4. Copy the **Redis URL** (format: `redis://user:pass@host:port`)

### Step 3: Deploy from Blueprint

1. Click **New** → **Web Service**
2. Choose **Deploy from Git → GitHub**
3. Select your repository: `alx-project-nexus`
4. Under "Advanced", paste the `render.yaml` blueprint configuration
5. Click **Create Web Service**

Render will parse `render.yaml` and automatically create:
- Web service (Django API with Gunicorn)
- Worker service (Celery worker for background tasks)
- Beat scheduler (Periodic task scheduling)

### Step 4: Get Deployment Hook URL

1. Go to your Web Service settings
2. Find **Deploy Hook** section
3. Copy the URL (looks like: `https://api.render.com/deploy/srv-xxxx?key=xxxx`)
4. Add this as `RENDER_DEPLOY_HOOK_URL` GitHub Secret

### Step 5: Configure Environment Variables in Render

In your **Web Service → Environment**:

```ini
DJANGO_SETTINGS_MODULE=config.settings
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com,www.your-app.onrender.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

Environment variables from GitHub Secrets:
- `TMDB_API_KEY` (from GitHub Secrets)
- `SECRET_KEY` (from GitHub Secrets)

---

## Environment Variables

### Required Variables (Production)

| Variable | Purpose | Example |
|---|---|---|
| `SECRET_KEY` | Django encryption key | `django-insecure-...` |
| `DEBUG` | Debug mode (ALWAYS False) | `False` |
| `ALLOWED_HOSTS` | Allowed domain names | `your-app.onrender.com` |
| `TMDB_API_KEY` | Movie database API key | `abc123...` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:password@host/db` |
| `REDIS_URL` | Redis cache URL | `redis://user:password@host:port` |
| `CELERY_BROKER_URL` | Celery message broker | `redis://:password@host:port/1` |
| `CELERY_RESULT_BACKEND` | Celery result storage | `redis://:password@host:port/2` |

### Security Variables (Auto-enabled on Production)

```python
# config/settings.py enables these when DEBUG=False:
SECURE_SSL_REDIRECT = True            # Redirect HTTP → HTTPS
SESSION_COOKIE_SECURE = True          # Only send cookies over HTTPS
CSRF_COOKIE_SECURE = True             # CSRF token over HTTPS only
SECURE_HSTS_SECONDS = 31536000        # HTTP Strict Transport Security (1 year)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True # HSTS applies to subdomains
SECURE_HSTS_PRELOAD = True            # Preload HSTS list
```

---

## Deployment Process

### Automatic Deployment (Recommended)

**Trigger**: Push to `main` branch with passing tests

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes & commit
git add .
git commit -m "feat: add new feature"

# 3. Push to GitHub
git push origin feature/my-feature

# 4. Create Pull Request
# → GitHub Actions runs tests automatically
# → If all tests pass (coverage ≥80%), merge to main

# 5. Push to main
git merge feature/my-feature
git push origin main

# 6. GitHub Actions:
#    ✅ Runs pytest with coverage gate (--cov-fail-under=80)
#    ✅ If pass: Triggers Render deployment hook
#    ✅ Render deploys new code to production
```

### Manual Deployment

If you need to redeploy without code changes:

1. Go to **Render Dashboard** → **Web Service**
2. Click **Manual Deploy** → **Deploy latest commit**
3. Watch deployment progress in Logs

### Viewing CI/CD Status

**GitHub Actions Workflow**:
```
Repository → Actions → CI/CD Pipeline
```

Displays:
- ✅ **test**: pytest runs, coverage report, coverage gate status
- ✅ **lint**: Code quality checks (flake8, black, isort)
- ✅ **deploy**: Render deployment hook trigger

**Render Deployment Logs**:
```
Render Dashboard → Web Service → Logs
```

Shows build output, migrations, and runtime errors.

---

## Post-Deployment Verification

### Health Check Endpoint

Test that API is responding:

```bash
curl https://your-app.onrender.com/api/health/
# Expected: {"status":"ok"}
```

### Admin Panel

Django admin should be accessible:

```bash
https://your-app.onrender.com/admin/
```

Login with superuser credentials (create during initial setup):

```bash
cd Movie-Recommendation-BE
python manage.py createsuperuser --settings=config.settings

# Then in production:
# ssh/connect to Render and run:
python manage.py createsuperuser
```

### Test API Endpoints

```bash
# List movies
curl https://your-app.onrender.com/api/movies/?limit=5

# Swagger documentation
https://your-app.onrender.com/api/docs/

# API schema
curl https://your-app.onrender.com/api/schema/
```

### Monitor Database

```bash
# Connect to Render PostgreSQL
psql postgresql://user:password@host:5432/db

# Check tables
\dt

# Verify migrations applied
SELECT * FROM django_migrations;
```

### Monitor Redis

```bash
# Connect to Render Redis
redis-cli -h host -p 6379 -a password

# Check usage
INFO memory

# Monitor commands
MONITOR
```

---

## Monitoring & Troubleshooting

### Common Issues

#### Issue: Tests fail with "No module named 'X'"

**Solution**: Ensure dependencies are in `requirements.txt`:

```bash
cd Movie-Recommendation-BE
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update requirements"
git push origin main
```

#### Issue: Coverage below 80%, deployment blocked

**Solution**: Add tests for uncovered code:

```bash
cd Movie-Recommendation-BE
pytest --cov=apps --cov-report=html
# Open htmlcov/index.html to identify gaps
# Add tests for uncovered lines
pytest --cov=apps --cov-fail-under=80  # Verify locally before push
```

#### Issue: Database migration fails in production

**Solution**: Check Render logs and apply migrations manually:

```bash
# Via Render shell (if available)
python manage.py migrate --settings=config.settings

# Or view migration logs:
# Render → Web Service → Logs → Search "migrate"
```

#### Issue: TMDb API key invalid / rate limited

**Solution**:

```bash
# Verify key in GitHub Secrets
# Settings → Secrets → TMDB_API_KEY

# Check usage:
# https://www.themoviedb.org/account/settings/api

# Rate limits: 40 requests/10 seconds (free tier)
# Upgrade API key for production load
```

### Monitoring in Production

**Render Dashboard Metrics**:
- CPU / Memory usage
- Request count & latency
- Error rates
- Logs in real-time

**Set up alerting** (Render Starter+ plans):
- Email notifications on build failures
- Crash detection

**Optional: Sentry Integration** (error tracking):

```python
# config/settings.py
if not DEBUG:
    import sentry_sdk
    sentry_sdk.init(
        dsn="https://key@sentry.io/project",
        traces_sample_rate=0.1,
        environment="production"
    )
```

---

## Rollback Procedure

If deployment breaks production:

### Option 1: Auto-Rollback (Render)

```
Render Dashboard → Web Service → Deployments
→ Click previous successful deployment → Rollback
```

### Option 2: Git Rollback

```bash
# Revert problematic commit
git revert HEAD
git push origin main

# GitHub Actions will run tests & redeploy
#(only deploys if tests pass)
```

### Option 3: Render Manual Rollback

```
Render → Web Service → Manual Deploy → Select older deployment
```

---

## Database Backups

Render databases include automated backups. To restore:

1. **Render Dashboard** → **PostgreSQL** → **Backups**
2. Click **Restore** on desired backup
3. Specify new database or overwrite current

For manual backups:

```bash
# Dump database
pg_dump postgresql://user:pass@host/db > backup.sql

# Restore
psql postgresql://user:pass@host/db < backup.sql
```

---

## Scaling & Performance

### Horizontal Scaling (Multiple Instances)

In Render settings, increase instance count or upgrade plan to enable auto-scaling.

### Optimize Database Queries

```bash
# Enable query logging
LOGGING_LEVEL=DEBUG

# Analyze slow queries
python manage.py shell
>>> from django.db import connection
>>> connection.queries  # Shows all SQL queries
```

### Cache Configuration

Production uses Redis caching. To purge cache:

```bash
redis-cli -h host -p 6379 -a password
> FLUSHDB  # Clear all cache
> FLUSHALL # Clear all databases
```

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Celery**: https://docs.celeryproject.io/

---

## Checklist for Production Launch

- [ ] All 3 GitHub Secrets configured (`TMDB_API_KEY`, `SECRET_KEY`, `RENDER_DEPLOY_HOOK_URL`)
- [ ] PostgreSQL database created in Render
- [ ] Redis instance created in Render
- [ ] `render.yaml` blueprint deployed to production
- [ ] Environment variables set in Render dashboard
- [ ] Health check endpoint responding: `/api/health/`
- [ ] Database migrations applied successfully
- [ ] Superuser account created
- [ ] Django admin panel accessible
- [ ] Swagger docs working: `/api/docs/`
- [ ] Test deployment with curl commands
- [ ] Monitor logs for 24 hours after launch
- [ ] Set up Sentry for error tracking (optional)
- [ ] Enable CI/CD auto-deployment on main branch

---

## Questions?

For deployment issues:

1. Check **Render Logs**: `Dashboard → Web Service → Logs`
2. Check **GitHub Actions**: `Repository → Actions → Latest Workflow`
3. Check `.env` file locally matches production variables
4. Verify `DJANGO_SETTINGS_MODULE=config.settings` (not settings_test)
5. Confirm `DEBUG=False` in production

Happy deploying! 🚀
