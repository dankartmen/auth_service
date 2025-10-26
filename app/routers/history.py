from typing import List
from fastapi import APIRouter, Depends, Body, HTTPException, Query
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/history", tags=["History"])

@router.post("/", response_model=schemas.ExerciseHistoryOut)
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

@router.delete("/{history_id}")
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
