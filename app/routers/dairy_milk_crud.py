from app.database import SessionLocal
from app.models import Users,Ranches,UserRanches, Dairy_Milk
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path, Query
from typing import Annotated,Optional,List
from starlette import status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from datetime import datetime,date


router = APIRouter(
    prefix='/milk',
    tags=['DairyMilk']
)

class DairyMilkInfoResponse(BaseModel):
    ranch_name: str
    milk_quality: float
    milk_quantity: float
    created_at: datetime
    updated_at: datetime

class DairyMilkRequest(BaseModel):
    ranch_id: int = Field(gt=0)
    milk_quality: float
    milk_quantity: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/' ,response_model= List[DairyMilkInfoResponse], status_code=status.HTTP_200_OK)
def get_dairy_milk_list_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'cheesemaker' or user.get('user_role') == 'rancher' or user.get('user_role') == 'vet':

        return db.query(UserRanches.user_id, Ranches.name.label('ranch_name'), Dairy_Milk.milk_quality.label('milk_quality'), Dairy_Milk.milk_quantity.label('milk_quantity'), Dairy_Milk.created_at.label('created_at'), Dairy_Milk.updated_at.label('updated_at')) \
            .join(Ranches, UserRanches.ranch_id == Ranches.id) \
            .join(Dairy_Milk, Ranches.id == Dairy_Milk.ranch_id) \
            .filter(UserRanches.user_id == user.get('user_id')).all()
    elif user.get('user_role') == 'admin':
        return db.query(UserRanches.user_id, Ranches.name.label('ranch_name'), Dairy_Milk.milk_quality.label('milk_quality'), Dairy_Milk.milk_quantity.label('milk_quantity'), Dairy_Milk.created_at.label('created_at'), Dairy_Milk.updated_at.label('updated_at')) \
                .join(Ranches, UserRanches.ranch_id == Ranches.id) \
                .join(Dairy_Milk, Ranches.id == Dairy_Milk.ranch_id).all()
    
@router.post('/' , status_code=status.HTTP_201_CREATED)
async def create_dairy_milk(user: user_dependency, db:db_dependency, dairymilkrequest:DairyMilkRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    dairy_milk_model = Dairy_Milk(
        ranch_id= dairymilkrequest.ranch_id,
        milk_quality = dairymilkrequest.milk_quality,
        milk_quantity = dairymilkrequest.milk_quantity,
        created_at = datetime.now(),
        updated_at = datetime.now(),
    )

    db.add(dairy_milk_model)
    db.commit()

@router.put('/{dairy_milk_id}' , status_code=status.HTTP_204_NO_CONTENT)
async def update_dairy_milk(user: user_dependency, db:db_dependency, update_dairy_milk_request:DairyMilkRequest, dairy_milk_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    dairy_milk_model = db.query(Dairy_Milk).filter(Dairy_Milk.id == dairy_milk_id).first()
    if dairy_milk_model is None:
        raise HTTPException(status_code=404, detail='Dairy milk record not found')
    dairy_milk_model.milk_quantity = update_dairy_milk_request.milk_quantity
    dairy_milk_model.milk_quality = update_dairy_milk_request.milk_quality
    dairy_milk_model.ranch_id = dairy_milk_model.ranch_id
    dairy_milk_model.updated_at = datetime.now()

    db.add(dairy_milk_model)
    db.commit()

@router.delete("/{dairy_milk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wellindex(user:user_dependency,db: db_dependency, dairy_milk_id: int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    dairy_milk_query = db.query(Dairy_Milk).filter(Dairy_Milk.id == dairy_milk_id).first
    if dairy_milk_query is None:
        raise HTTPException(status_code=404, detail='Dairy milk record not found.')

    db.query(Dairy_Milk).filter(Dairy_Milk.id == dairy_milk_id).delete()
    db.commit()

