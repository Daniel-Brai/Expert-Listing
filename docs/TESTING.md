# Testing Guide

This document provides instructions for running tests in the Expert Listing application.

## Prerequisites

- Python 3.14+
- PostgreSQL with PostGIS extension
- Docker and Docker Compose (for containerized testing)

## Running Tests in Docker

Running tests in Docker ensures a consistent environment and isolates test execution.

### Setup

1. **Run tests:**

   ```bash
   make test
   ```

   Or directly with docker compose:

   ```bash
	docker compose run --remove-orphans backend bash -c "uv run pytest -n auto ./tests"
   ```
