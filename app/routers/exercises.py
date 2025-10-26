from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/exercises", tags=["Exercises"])

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