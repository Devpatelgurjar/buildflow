from fastapi import FastAPI
from dotenv import load_dotenv
from app.models.base import Base
from app.models.user import User
from app.core.database import engine
from app.api.auth import router as auth_router
from app.api.project import router as project_router
from app.api.chat import router as chat_router

load_dotenv()

# Try to create tables, but don't fail if database is not available
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not initialize database: {e}")

app = FastAPI()
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "Hello World from builflow"
    }