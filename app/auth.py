from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import models, schemas
from app.database import get_db, init_db
from typing import List, Optional
from sqlalchemy import cast, func, String

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
            models.Questionnaire.user_id == user.id
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
        raise HTTPException(status_code=403, detail="Forbidden")

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
        raise HTTPException(status_code=403, detail="Forbidden")

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
        raise HTTPException(status_code=404, detail="History item not found")

    if history_item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(history_item)
    db.commit()
    return {"message": "History item deleted"}
