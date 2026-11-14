# Database Migrations

This directory contains Alembic migration scripts and documentation for the PostgreSQL database schema.

## Commands

Initialize migration environment:
```powershell
alembic init backend/database/migrations
```

Create a new migration:
```powershell
alembic revision --autogenerate -m "create_initial_schema"
```

Apply migrations:
```powershell
alembic upgrade head
```

