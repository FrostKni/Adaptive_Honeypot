# Database Migrations Guide

This document describes how to manage database migrations using Alembic for the Adaptive Honeypot System.

## Overview

The Adaptive Honeypot System uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations. This allows for:
- Version-controlled database schema changes
- Easy schema upgrades and downgrades
- Automatic migration generation from SQLAlchemy models
- Support for both SQLite (development) and PostgreSQL (production)

## Prerequisites

Alembic is installed as a dependency. Ensure you have:
- Python 3.11+
- SQLAlchemy 2.0+
- Database drivers:
  - Development: `aiosqlite` (SQLite async)
  - Production: `asyncpg` (PostgreSQL async), `psycopg2` (PostgreSQL sync for migrations)

## Configuration

### Database Connection

Database connection settings are managed in `src/core/config.py` and can be overridden via environment variables:

**SQLite (Default - Development):**
```bash
DB_TYPE=sqlite
```

**PostgreSQL (Production):**
```bash
DB_TYPE=postgres
DB_HOST=your-db-host
DB_PORT=5432
DB_USER=honeypot_user
DB_PASSWORD=secure_password
DB_NAME=adaptive_honeypot
```

### Alembic Configuration

The `alembic.ini` file contains Alembic configuration. The database URL is automatically set from application settings in `migrations/env.py`.

## Common Commands

### Create a New Migration

**Auto-generate from model changes:**
```bash
python3 -m alembic revision --autogenerate -m "description_of_change"
```

**Create empty migration (for custom SQL):**
```bash
python3 -m alembic revision -m "description_of_change"
```

### Apply Migrations

**Apply all pending migrations:**
```bash
python3 -m alembic upgrade head
```

**Apply specific migration:**
```bash
python3 -m alembic upgrade <revision_id>
```

**Apply next migration:**
```bash
python3 -m alembic upgrade +1
```

### Rollback Migrations

**Rollback last migration:**
```bash
python3 -m alembic downgrade -1
```

**Rollback to specific revision:**
```bash
python3 -m alembic downgrade <revision_id>
```

**Rollback all migrations:**
```bash
python3 -m alembic downgrade base
```

### View Migration Status

**Current migration version:**
```bash
python3 -m alembic current
```

**Migration history:**
```bash
python3 -m alembic history
```

**Pending migrations:**
```bash
python3 -m alembic show head
```

## Migration Files

### Location

Migration files are stored in `migrations/versions/` and follow the naming pattern:
```
<revision_hash>_<description>.py
```

Example: `bd73bd710c30_001_initial_schema.py`

### Structure

Each migration file contains:

```python
"""description_of_change

Revision ID: <revision_id>
Revises: <parent_revision>
Create Date: <timestamp>
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '<revision_id>'
down_revision = '<parent_revision>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Upgrade logic
    pass


def downgrade() -> None:
    # Downgrade logic
    pass
```

### Initial Schema Migration

The initial migration (`001_initial_schema`) creates all core tables:

- `honeypots` - Honeypot instances
- `sessions` - Attack sessions
- `attack_events` - Individual attack events
- `adaptations` - Honeypot adaptation records
- `health_records` - Honeypot health metrics
- `alerts` - Security alerts
- `threat_intelligence` - Threat intelligence data
- `api_keys` - API authentication keys
- `audit_logs` - Audit trail
- `cognitive_profiles` - Cognitive analysis data
- `deception_events` - Deception strategy records

## Development Workflow

### 1. Modify Models

Make changes to SQLAlchemy models in `src/core/db/models.py`.

### 2. Generate Migration

```bash
python3 -m alembic revision --autogenerate -m "add_new_table_or_column"
```

### 3. Review Migration

Always review the generated migration file before applying:
- Check that all changes are correct
- Verify indexes and constraints
- Ensure data migrations are handled if needed

### 4. Test Migration

```bash
# Apply migration
python3 -m alembic upgrade head

# Test your application
pytest tests/

# Rollback if needed
python3 -m alembic downgrade -1
```

### 5. Commit

```bash
git add migrations/versions/<new_migration>.py
git commit -m "Add migration: add_new_table_or_column"
```

## Production Deployment

### Pre-deployment Checklist

1. **Backup Database**
   ```bash
   # PostgreSQL
   pg_dump adaptive_honeypot > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # SQLite
   cp honeypot.db honeypot.db.backup
   ```

2. **Test Migration Locally**
   ```bash
   # Use a copy of production data
   python3 -m alembic upgrade head
   python3 -m alembic downgrade base
   python3 -m alembic upgrade head
   ```

3. **Check Migration Status**
   ```bash
   python3 -m alembic current
   python3 -m alembic history
   ```

### Deploying Migrations

1. **Stop Application**
   ```bash
   # Stop the application to prevent concurrent schema changes
   systemctl stop adaptive-honeypot
   ```

2. **Run Migrations**
   ```bash
   python3 -m alembic upgrade head
   ```

3. **Verify Migration**
   ```bash
   python3 -m alembic current
   ```

4. **Start Application**
   ```bash
   systemctl start adaptive-honeypot
   ```

### Rollback Procedure

If migration causes issues:

1. **Stop Application**
   ```bash
   systemctl stop adaptive-honeypot
   ```

2. **Rollback Migration**
   ```bash
   python3 -m alembic downgrade -1  # Or specific revision
   ```

3. **Restore Backup (if needed)**
   ```bash
   # PostgreSQL
   psql adaptive_honeypot < backup_20260406_120000.sql
   
   # SQLite
   cp honeypot.db.backup honeypot.db
   ```

4. **Restart Application**
   ```bash
   systemctl start adaptive-honeypot
   ```

## Best Practices

### Migration Design

1. **Keep Migrations Small**
   - One logical change per migration
   - Easier to review, test, and rollback

2. **Make Migrations Reversible**
   - Always implement both `upgrade()` and `downgrade()`
   - Test both directions

3. **Handle Data Migrations Carefully**
   - Large data changes should be done in batches
   - Consider running data migrations as separate scripts

4. **Add Indexes Explicitly**
   - Don't rely on autogenerate for indexes
   - Add indexes in separate migrations if tables are large

### Naming Conventions

- Use descriptive names: `add_user_email_column`, not `update_table`
- Prefix with action: `add_`, `remove_`, `update_`, `create_`, `drop_`
- Include table/model name

### Testing

- Test migrations with sample data
- Verify application works after upgrade
- Verify application works after downgrade
- Check for performance issues with large datasets

## Troubleshooting

### "Can't locate revision identified by '<revision_id>'"

The migration history is inconsistent. Fix by:
```bash
# Check current state
python3 -m alembic current
python3 -m alembic history

# Stamp to correct version if needed
python3 -m alembic stamp head
```

### "Target database is not up to date"

Apply pending migrations:
```bash
python3 -m alembic upgrade head
```

### "Multiple root nodes" Error

Migration branches exist. Resolve by:
```bash
# View branches
python3 -m alembic heads

# Merge branches
python3 -m alembic merge -m "merge_branches" <head1> <head2>
```

### SQLite Limitations

SQLite has limited ALTER TABLE support. For complex migrations:
1. Create new table with desired schema
2. Copy data from old table
3. Drop old table
4. Rename new table

Example:
```python
def upgrade():
    # Create new table
    op.create_table('honeypots_new', ...)
    
    # Copy data
    op.execute("INSERT INTO honeypots_new SELECT * FROM honeypots")
    
    # Drop old table
    op.drop_table('honeypots')
    
    # Rename
    op.rename_table('honeypots_new', 'honeypots')
```

## Environment Variables

Key environment variables for migrations:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_TYPE` | Database type (`sqlite` or `postgres`) | `sqlite` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | PostgreSQL user | `honeypot` |
| `DB_PASSWORD` | PostgreSQL password | `honeypot_secret` |
| `DB_NAME` | Database name | `adaptive_honeypot` |

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [Database Migration Best Practices](https://github.com/AscentSoftware/ascent-migrations-best-practices)

## Support

For issues with migrations:
1. Check this documentation
2. Review Alembic documentation
3. Check application logs
4. Contact the development team
