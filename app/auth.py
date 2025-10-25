from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import models, schemas
from app.database import get_db, init_db
from typing import List, Optional, Dict
from sqlalchemy import cast, func, String
from datetime import datetime,timedelta

router = APIRouter()
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

init_db()

def authenticate(credentials: HTTPBasicCredentials, db: Session):
    user = db.query(models.User).filter(
        models.User.username == credentials.username
    ).first()

    if not user or not pwd_context.verify(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
         detail="Invalid credentials",
         headers={"WWW-Authenticate": "Basic"},
        )
    return user

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    return authenticate(credentials, db)


@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, password=hashed_password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "id": db_user.id,
        "username": db_user.username
    }

@router.get("/login")
def login(user: models.User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username
    }

@router.post("/reset-password")
def reset_password(
    username: str = Body(..., embed=True),
    new_password: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    # Находим пользователя по имени пользователя
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        # В целях безопасности не сообщаем, что пользователь не найден
        print("Если пользователь существует, пароль был изменен")
        return {"message": "Если пользователь существует, пароль был изменен"}
    # Хешируем новый пароль
    hashed_password = pwd_context.hash(new_password)
    user.password = hashed_password
    db.commit()
    print("Пароль успешно изменен")
    return {"message": "Пароль успешно изменен"}


@router.post("/questionnaires", response_model=schemas.QuestionnaireOut)
def create_questionnaire(
    questionnaire: schemas.QuestionnaireCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"User ID: {current_user.id}")
        print(f"User exists: {db.query(models.User).get(current_user.id) is not None}")
	    print(f"Saving the questionnaire for the user ID: {current_user.id}")
	    print(f"Questionnaire data : {questionnaire.dict()}")
        # проверка существования анкеты
        existing = db.query(models.Questionnaire).filter(
            models.Questionnaire.user_id == current_user.id
        ).first()

        if existing:
            for key, value in questionnaire.dict().items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            db_questionnaire = models.Questionnaire(
                user_id=user_id,
                **questionnaire.dict()
            )
            db.add(db_questionnaire)
            db.commit()
            db.refresh(db_questionnaire)
            return db_questionnaire
    except Exception as e:
         db.rollback()
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/questionnaire", response_model=schemas.QuestionnaireOut)
def get_questionnaire(
    user_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    questionnaire = db.query(models.Questionnaire).filter(
        models.Questionnaire.user_id == user_id
    ).first()

    if not questionnaire:
        raise HTTPException(status_code=404, detail="Анкета не найдена")
    else:
        return questionnaire

@router.get("/debug-exercises", response_model=List[schemas.ExerciseOut])
def debug_exercises(db: Session = Depends(get_db)):
    try:
        exercises = db.query(models.Exercise).all()

        print(f"Len : {len(exercises)}")
        for ex in exercises:
            print(f"ID: {ex.id}, Title: {ex.title}")
            print(f"Suitable for: {ex.suitable_for}")
            print(f"Max pain: {ex.max_pain_level}")

        return exercises
    except Exception as e:
        print(f"  debug_exercises: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/exercises", response_model=list[schemas.ExerciseOut])
def get_exercises(
    injury_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Получаем ВСЕ упражнения из базы
    all_exercises = db.query(models.Exercise).all()

    # Если указан тип травмы - фильтруем
    if injury_type:
        # Приводим к нижнему регистру для регистронезависимого сравнения
        injury_lower = injury_type.lower()

        # Фильтруем упражнения
        filtered_exercises = [
            ex for ex in all_exercises
            if ex.suitable_for and any(
                injury_lower == s.lower() for s in ex.suitable_for
            )
        ]

        # Отладочный вывод
        print(f"Найдено упражнений после фильтрации: {len(filtered_exercises)}")
        for ex in filtered_exercises:
            print(f"Упражнение {ex.id} подходит для '{injury_type}'")

        return filtered_exercises

    # Если тип травмы не указан - возвращаем все упражнения
    return all_exercises

@router.get("/{exercise_id}", response_model=schemas.ExerciseOut)
def get_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(models.Exercise).get(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@router.post("/history", response_model=schemas.ExerciseHistoryOut)
def add_exercise_history(
    history: schemas.ExerciseHistoryCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем, что пользователь добавляет свою историю
    if current_user.id != history.user_id:
        raise HTTPException(status_code=403, detail="Запрещено")

    db_history = models.ExerciseHistory(**history.dict())
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

@router.get("/users/{user_id}/history", response_model=List[schemas.ExerciseHistoryOut])
def get_exercise_history(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем права доступа
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Запрещено")

    return db.query(models.ExerciseHistory).filter(
        models.ExerciseHistory.user_id == user_id
    ).order_by(models.ExerciseHistory.date_time.desc()).all()

@router.delete("/history/{history_id}")
def delete_exercise_history(
    history_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    history_item = db.query(models.ExerciseHistory).get(history_id)
    if not history_item:
        raise HTTPException(status_code=404, detail="Элемент история не найден")

    if history_item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Запрещено")

    db.delete(history_item)
    db.commit()
    return {"message": "Элемент истории удалён"}


def get_exercise_frequency(title: str) -> Dict[str, int]:

    frequencies = {
        "Изометрическое напряжение мышц": {'times_per_day': 3, 'days_per_week': 7},
        "Нейропластическая гимнастика": {'times_per_day': 2, 'days_per_week': 5},
        "Пассивная разработка сустава": {'times_per_day': 2, 'days_per_week': 6},
        "Дыхательная гимнастика": {'times_per_day': 5, 'days_per_week': 7},
        "Тренировка мелкой моторики": {'times_per_day': 2, 'days_per_week': 7},
        "Растяжка ахиллова сухожилия": {'times_per_day': 1, 'days_per_week': 3},
        "Стабилизация плечевого сустава": {'times_per_day': 2, 'days_per_week': 4},
        "Восстановление мышц живота": {'times_per_day': 3, 'days_per_week': 5},
        "Дыхание с сопротивлением": {'times_per_day': 4, 'days_per_week': 7},
        "Аквааэробика": {'times_per_day': 1, 'days_per_week': 3},
        "Баланс-терапия": {'times_per_day': 2, 'days_per_week': 5},
    }
    return frequencies.get(title, {'times_per_day': 1, 'days_per_week': 3})

def should_add_training(date: datetime, frequency: Dict[str, int]) -> bool:
    """Перенос логики _shouldAddTraining"""
    day_of_week = date.weekday()  # 1=Пн, 7=Вс
    times_per_day = frequency['times_per_day']
    days_per_week = frequency['days_per_week']
    is_training_day = day_of_week <= days_per_week
    return is_training_day and (date.day % (7 // times_per_day if times_per_day > 0 else 1) == 0)

@router.post("/schedules", response_model=schemas.TrainingScheduleOut)
def generate_schedule(
    create_data: schemas.TrainingScheduleCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Проверяем анкету
    questionnaire = db.query(models.Questionnaire).filter(
        models.Questionnaire.id == create_data.questionnaire_id,
        models.Questionnaire.user_id == current_user.id
    ).first()
    print(f"Ищем анкету ID={create_data.questionnaire_id} для user_id={currrent_user.id}")
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Анкета не найдена")

    print(f"DEBUG: Injury type: '{questionnaire.main_injury_type}', specific: '{questionnaire.specific_injury}'")
    # Получаем ВСЕ упражнения из базы
    all_exercises = db.query(models.Exercise).all()

    specific_injury = questionnaire.specific_injury
    # Загружаем упражнения по specific_injury
    exercises = [
        exercise for exercise in all_exercises
        if any(specific_injury in str(item) for item in exercise.suitable_for or [])
    ]

    print(f"DEBUG: Подходящих упражнений: {len(exercises)}, titles={[e.title for e in exercises]}")
    if not exercises:
        raise HTTPException(status_code=404, detail="Нет подходящих упражнений")

    # Создаем расписание
    schedule = models.TrainingSchedule(
        user_id=current_user.id,
        questionnaire_id=questionnaire.id,
        injury_type=questionnaire.main_injury_type,
        specific_injury=questionnaire.specific_injury
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    # Генерируем тренировки на 84 дня
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = current_date + timedelta(days=84)

    while current_date < end_date:
        for exercise in exercises:
            frequency = get_exercise_frequency(exercise.title)
            if should_add_training(current_date, frequency):
                # Время: простая логика (9:00 + offset)
                time_offset = len([e for e in exercises if should_add_training(current_date, get_exercise_frequency(e.title))]) * 30  # 30 мин интервал
                training_time = f"{9 + (time_offset // 60):02d}:{(time_offset % 60):02d}"

                training = models.Training(
                    schedule_id=schedule.id,
                    exercise_id=exercise.id,
                    date=current_date,
                    time=training_time,
                    is_completed=False
                )
                db.add(training)
        current_date += timedelta(days=1)

    db.commit()
    # Перезагружаем для возврата с тренировками
    db.refresh(schedule)
    return schedule

@router.get("/users/{user_id}/schedules", response_model=List[schemas.TrainingScheduleOut])
def get_schedules(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    schedules = db.query(models.TrainingSchedule).filter(
        models.TrainingSchedule.user_id == user_id,
        models.TrainingSchedule.is_active == True
    ).all()
    for schedule in schedules:
        schedule.trainings = db.query(models.Training).filter(
            models.Training.schedule_id == schedule.id
        ).all()
    return schedules

@router.put("/schedules/{schedule_id}/trainings/{training_id}", response_model=schemas.TrainingOut)
def update_training_status(
    schedule_id: int,
    training_id: int,
    is_completed: bool = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule = db.query(models.TrainingSchedule).filter(
        models.TrainingSchedule.id == schedule_id,
        models.TrainingSchedule.user_id == current_user.id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")

    training = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.schedule_id == schedule_id
    ).first()
    if not training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    training.is_completed = is_completed
    training.completed_at = datetime.utcnow() if is_completed else None
    db.commit()
    db.refresh(training)
    return training

@router.get("/schedules/{schedule_id}/trainings", response_model=List[schemas.TrainingOut])
def get_trainings_for_schedule(
    schedule_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule = db.query(models.TrainingSchedule).filter(
        models.TrainingSchedule.id == schedule_id,
        models.TrainingSchedule.user_id == current_user.id
    ).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    return db.query(models.Training).filter(models.Training.schedule_id == schedule_id).all()

@router.post("/schedules/{schedule_id}/trainings", response_model=schemas.TrainingOut)
def create_training(schedule_id: int, training: schemas.TrainingCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    schedule = db.query(models.TrainingSchedule).filter(models.TrainingSchedule.id == schedule_id, models.TrainingSchedule.user_id == current_user.id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    db_training = models.Training(**training.dict(), schedule_id=schedule_id)
    db.add(db_training)
    db.commit()
    db.refresh(db_training)
    return db_training

@router.put("/schedules/{schedule_id}/trainings/{training_id}", response_model=schemas.TrainingOut)
def update_training(schedule_id: int, training_id: int, training_update: schemas.TrainingOut, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Аналогично update_training_status, но обновляйте все поля
    training = db.query(models.Training).filter(models.Training.id == training_id, models.Training.schedule_id == schedule_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    for key, value in training_update.dict(exclude_unset=True).items():
        setattr(training, key, value)
    db.commit()
    db.refresh(training)
    return training

@router.delete("/schedules/{schedule_id}/trainings/{training_id}")
def delete_training(schedule_id: int, training_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    training = db.query(models.Training).filter(models.Training.id == training_id, models.Training.schedule_id == schedule_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    db.delete(training)
    db.commit()
    return {"message": "Удалено"}