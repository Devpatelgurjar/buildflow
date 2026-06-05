# Alembic database migration configuration
# Configure this directory for Alembic migrations

# alembic init workflow:
# 1. alembic init alembic  
# 2. Configure sqlalchemy.url in alembic.ini
# 3. Add your models to env.py target_metadata
# 4. Create initial migration: alembic revision --autogenerate -m "initial"
# 5. Apply migration: alembic upgrade head
