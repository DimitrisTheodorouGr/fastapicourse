from starlette import status
from .auth import get_current_user
from app.database import SessionLocal
from app.models import Users, UserRanches, Ranches
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(
    prefix="/admin",
    tags=['Admin']
)
#Function for opening and closing connection with the database after each query.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/ranch_associations')
async def get_user_ranch_associations(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        # Perform the query
        results = (
            db.query(
                Users.username,
                Users.role,
                Ranches.name.label('ranch_name'),
                Ranches.id.label('ranch_id'),
                Users.id.label('user_id')
            )
            .join(UserRanches, UserRanches.user_id == Users.id)
            .join(Ranches, UserRanches.ranch_id == Ranches.id)
            .all()
        )

        # Transform the results into a list of dictionaries to return as JSON
        output = [
            {
                "username": result.username,
                "ranch_name": result.ranch_name,
                "user_role":result.role,
                "ranch_id": result.ranch_id,
                "user_id": result.user_id
            }
            for result in results
        ]
        return output

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: user_dependency, db: db_dependency, user_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        user_model = db.query(Users).filter(Users.id == user_id).first()
        if user_model is None:
            raise HTTPException(status_code=404, detail='User not found.')

        db.query(Users).filter(Users.id == user_id).delete()
        db.commit()
    else:
     return {'message': 'Only admins can delete'}