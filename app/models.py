from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    schedules = relationship("TrainingSchedule", back_populates="user")
    
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

class TrainingSchedule(Base):
    __tablename__ = "training_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    questionnaire_id = Column(Integer, ForeignKey("questionnaires.id"), nullable=False)  # Связь с анкетой
    injury_type = Column(String, nullable=False)  # main_injury_type из анкеты
    specific_injury = Column(String, nullable=False)  # specific_injury из анкеты
    generated_at = Column(DateTime, default=datetime.utcnow) # точное время создания записи в UTC
    is_active = Column(Boolean, default=True)  # Чтобы можно было деактивировать старые расписания

    # Связи
    user = relationship("User", back_populates="schedules")
    questionnaire = relationship("Questionnaire")
    trainings = relationship("Training", back_populates="schedule", cascade="all, delete-orphan")

class Training(Base):
    __tablename__ = "trainings"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("training_schedules.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    date = Column(DateTime)  # Дата тренировки (без времени, только день)
    time = Column(String(5))  # Время как строка, напр. "09:00" (перенесено из TimeOfDay)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)  # Когда отмечено как выполненное

    # Связи
    schedule = relationship("TrainingSchedule", back_populates="trainings")
    exercise = relationship("Exercise")