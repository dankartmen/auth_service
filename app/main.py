from fastapi import FastAPI
from app.database import init_db
from app.routers import auth, exercises, history, questionnaires, schedules

app = FastAPI(title="Health App API", version="0.0.1")

init_db()

app.include_router(auth.router)
app.include_router(questionnaires.router)
app.include_router(schedules.router)
app.include_router(history.router)  
app.include_router(exercises.router)