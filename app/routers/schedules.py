from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List
from app.dependencies import get_current_user
from app import models, schemas
from app.database import get_db
from datetime import datetime, timedelta


router = APIRouter(prefix="/schedules", tags=["Schedules"])

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

@router.post("/", response_model=schemas.TrainingScheduleOut)
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
    print(f"Ищем анкету ID={create_data.questionnaire_id} для user_id={current_user.id}")
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

@router.put("/{schedule_id}/trainings/{training_id}", response_model=schemas.TrainingOut)
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

@router.get("/{schedule_id}/trainings", response_model=List[schemas.TrainingOut])
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

@router.post("/{schedule_id}/trainings", response_model=schemas.TrainingOut)
def create_training(schedule_id: int, training: schemas.TrainingCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    schedule = db.query(models.TrainingSchedule).filter(models.TrainingSchedule.id == schedule_id, models.TrainingSchedule.user_id == current_user.id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    db_training = models.Training(**training.dict(), schedule_id=schedule_id)
    db.add(db_training)
    db.commit()
    db.refresh(db_training)
    return db_training

@router.put("/{schedule_id}/trainings/{training_id}", response_model=schemas.TrainingOut)
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

@router.delete("/{schedule_id}/trainings/{training_id}")
def delete_training(schedule_id: int, training_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    training = db.query(models.Training).filter(models.Training.id == training_id, models.Training.schedule_id == schedule_id).first()
    if not training:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    db.delete(training)
    db.commit()
    return {"message": "Удалено"}