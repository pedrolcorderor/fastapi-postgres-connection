from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from scalar_fastapi import get_scalar_api_reference


app =FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title= app.title + "- Scalar",
    )


class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool


class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

class ChoiceUpdate(BaseModel):
    choice_text: str

class QuestionUpdate(BaseModel):
    question_text: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close


db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/questions/{question_id}")
async def read_question(question_id: int, db: db_dependency):
    result = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail='Question is not  found')
    return result

@app.get("/choices/{question_id}")
async def read_choices(question_id: int, db: db_dependency ):
    result =db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    
    if not result:
        raise HTTPException(status_code=404, detail='Choices is not found')
    return result

@app.post("/questions/")
async def create_questions(question: QuestionBase, db: db_dependency):
    db_question = models.Questions(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=db_question.id)
        db.add(db_choice)
    db.commit()

@app.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: db_dependency):
    question = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail='Question not found')
    
    db.delete(question)
    db.commit()
    
    return {"detail": "Question deleted"}



@app.put("/choices/{choice_id}")
async def update_choice(choice_id: int, choice: ChoiceUpdate, db: db_dependency):
    db_choice = db.query(models.Choices).filter(models.Choices.id == choice_id).first()
    
    if not db_choice:
        raise HTTPException(status_code=404, detail='Choice not found')
    
    db_choice.choice_text = choice.choice_text
    db.commit()
    
    return {"detail": "Choice updated"}

@app.put("/questions/{question_id}")
async def update_questions(question_id: int , question: QuestionUpdate, db:db_dependency):
    db_question = db.query(models.Questions).filter(models.Questions.id == question_id).first()

    if not db_question:
        raise HTTPException(status_code=404, detail='Questions not found')

    db_question.question_text= question.question_text
    db.commit()
    return {"detail": "Question updated"}
