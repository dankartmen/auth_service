from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from app import models
    from app.exercise_init import init_db as init_db_data
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        init_db_data(db)
    except Exception as e:
        print(f"Exception db init: {e}")
        raise
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()