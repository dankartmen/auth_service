from fastapi import APIRouter, Depends,  HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])

@router.post("/", response_model=schemas.QuestionnaireOut)
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
                user_id=current_user.id,
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