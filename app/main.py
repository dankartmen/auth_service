from fastapi import FastAPI
from .database import engine, Base
from . import auth

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)