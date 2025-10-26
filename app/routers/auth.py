from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app import models, schemas
from app.database import get_db
from typing import List


router = APIRouter()
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



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

