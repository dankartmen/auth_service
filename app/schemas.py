from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

class QuestionnaireCreate(BaseModel):
    name: str
    gender: str
    weight: float
    height: float
    main_injury_type: str
    specific_injury: str
    pain_level: int
    training_time: str

    model_config = ConfigDict(from_attributes=True)
    
class QuestionnaireOut(QuestionnaireCreate):
    id: int
    user_id: int

class ExerciseBase(BaseModel):
    title: str
    general_description: str
    injury_specific_info: dict
    suitable_for: list[str]
    max_discomfort_level: int
    steps: list[str]
    tags: list[str]
    image_url: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    pass

class ExerciseOut(BaseModel):
    id: int
    title: str
    general_description: str
    injury_specific_info: Dict[str, str]
    suitable_for: List[str]
    max_pain_level: int
    steps: List[str]
    tags: List[str]
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ExerciseHistoryBase(BaseModel):
    exercise_name: str
    date_time: datetime
    duration: int
    notes: Optional[str] = None
    sets: int
    pain_level: int

class ExerciseHistoryCreate(ExerciseHistoryBase):
    user_id: int

class ExerciseHistoryOut(ExerciseHistoryBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class TrainingScheduleCreate(BaseModel):
    questionnaire_id: int  # ID анкеты для генерации

class TrainingScheduleOut(BaseModel):
    id: int
    user_id: int
    questionnaire_id: int
    injury_type: str
    specific_injury: str
    generated_at: datetime
    is_active: bool

    trainings: List['TrainingOut'] = []  # Вложенные тренировки 

    model_config = ConfigDict(from_attributes=True)

class TrainingCreate(BaseModel):
    exercise_id: int
    date: datetime
    time: str  # "HH:MM"
    is_completed: bool = False

class TrainingOut(BaseModel):
    id: int
    schedule_id: int
    exercise_id: int
    date: datetime
    time: str
    is_completed: bool
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Для полного расписания 
class FullScheduleOut(BaseModel):
    schedule: TrainingScheduleOut
    exercises: Dict[int, str]  # exercise_id -> title (для фронта)