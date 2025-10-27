from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import bcrypt
from app.database import get_db
from app import models

security = HTTPBasic()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля с помощью прямой библиотеки bcrypt"""
    try:
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def authenticate(credentials: HTTPBasicCredentials, db: Session):
    user = db.query(models.User).filter(
        models.User.username == credentials.username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Используем прямую проверку bcrypt
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    return authenticate(credentials, db)