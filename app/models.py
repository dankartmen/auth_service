from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, JSON, DateTime
from app.database import Base
from datetime import datetime
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String)
    gender = Column(String)
    weight = Column(Float)
    height = Column(Float)
    main_injury_type = Column(String)
    specific_injury = Column(String)
    pain_level = Column(Integer)
    training_time = Column(String)

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    general_description = Column(Text)
    injury_specific_info = Column(JSON)
    suitable_for = Column(JSON)
    max_pain_level = Column(Integer)
    steps = Column(JSON)
    tags = Column(JSON)
    image_url = Column(String(500), nullable=True)

class ExerciseHistory(Base):
    __tablename__ = "exercise_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_name = Column(String, nullable=False)
    date_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration = Column(Integer, nullable=False)  # в секундах
    notes = Column(Text, nullable=True)
    sets = Column(Integer, nullable=False, default=1)
    pain_level = Column(Integer, nullable=False, default=0)