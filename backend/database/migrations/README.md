# Database Migrations

This directory contains Alembic migration scripts for the PostgreSQL database schema.

## Prerequisites

- PostgreSQL must be running.
- DATABASE_URL must be configured in the project's `.env` file.
- Python dependencies must be installed.

## Create a Migration

Generate a migration from the SQLAlchemy models:

```powershell
alembic revision --autogenerate -m "create_initial_schema"