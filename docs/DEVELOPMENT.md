# Development Guide

This guide will help you set up and run the Expert Listing application for local development.

## Prerequisites

- Python 3.14+
- PostgreSQL 18+ with PostGIS extension
- [uv](https://docs.astral.sh/uv/) package manager
- Docker and Docker Compose ( for containerized development)

**NOTE**: Seeds to the database are run via an environment variable `APP_RUN_SEEDS` and by default it is set to be True

## Docker Development Setup

For a fully containerized development environment:

### 1. Start Services

**Start all services:**

```bash
docker compose up
```

**Start in detached mode:**

```bash
docker compose up -d
```

**Build and start:**

```bash
docker compose up --build
```

### 2. View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f postgres
```

### 3. Stop Services

```bash
# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes
docker compose down -v --remove-orphans
```

Navigate to `http://localhost:8000/docs` to access the application.


## Development Workflow

### Project Structure

```
expert_listing/
├── app/
│   ├── core/                    # Core application configuration
│   ├── database/                # Database utilities and mixins
│   ├── migrations/              # Alembic migrations
│   ├── shared/                  # Shared utilities and types
│   ├── src/                     # Application modules
│   │   ├── properties/          # Properties domain
│   │   └── geo_buckets/         # Geo buckets domain
│   ├── tests/                   # Test suite
│   ├── main.py                  # Application entry point
│   └── bootstrap.py             # Application factory
├── docker/                      # Docker configuration files
├── scripts/                     # Utility scripts
├── docs/                        # Documentation
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile                   # Application Dockerfile
└── Makefile                     # Development commands
```

### Common Tasks

#### Create a Database Migration

```bash
make revision M="description of changes"
```

#### Apply Migrations

```bash
make migrate
```

#### Run Tests in Docker

```bash
make test
```

#### Sync Dependencies

```bash
make sync
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

Or change the port in `.env.docker`:

```bash
APP_PORT=8001
```

### Database Connection Issues

1. **Check PostgreSQL is running:**

   ```bash
   pg_isready -h localhost -p 5432
   ```

2. **Verify connection string:**

   ```bash
   cd app
   uv run python -c "from core.settings import settings; print(settings.SQLALCHEMY_DATABASE_URI)"
   ```

3. **Test connection:**

   ```bash
   psql -h localhost -U postgres -d expert_listing_local
   ```

### Docker Issues

1. **Check container status:**

   ```bash
   docker compose ps
   ```

2. **View container logs:**

   ```bash
   docker compose logs backend
   docker compose logs postgres
   ```

3. **Restart services:**

   ```bash
   docker compose restart
   ```

4. **Clean rebuild:**

   ```bash
   docker compose down -v
   docker compose build --no-cache
   docker compose up
   ```

### Migration Issues

1. **Check current migration status:**

   ```bash
   cd app
   uv run alembic current
   ```

2. **View migration history:**

   ```bash
   cd app
   uv run alembic history
   ```

3. **Reset database (⚠️ destroys data):**

   ```bash
   cd app
   uv run alembic downgrade base
   uv run alembic upgrade head
   ```
