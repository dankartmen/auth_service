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

    print(f"Password length: {len(user.password)}")
    print(f"Password bytes: {len(user.password.encode('utf-8'))}")
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


