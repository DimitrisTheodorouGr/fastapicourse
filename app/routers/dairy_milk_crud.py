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
    dairy_milk_id: int
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

@router.get('/' ,response_model=List[DairyMilkInfoResponse], status_code=status.HTTP_200_OK)
def get_dairy_milk_list_based_on_role(user: user_dependency, db: db_dependency,
    limit: Optional[int] = Query(50, title="Max number of data returned", ge=0),
    start_date: Optional[date] = Query(None, title="Start date of the range"),
    end_date: Optional[date] = Query(None, title="End date of the range")):

    print(f"User Role: {user.get('user_role')}, User ID: {user.get('user_id')}")
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    # Base query for dairy milk data
    query = db.query(
        Dairy_Milk.id.label('dairy_milk_id'),
        Ranches.name.label('ranch_name'),
        Dairy_Milk.milk_quality.label('milk_quality'),
        Dairy_Milk.milk_quantity.label('milk_quantity'),
        Dairy_Milk.created_at.label('created_at'),
        Dairy_Milk.updated_at.label('updated_at')
    ).join(Ranches, Dairy_Milk.ranch_id == Ranches.id) \
     .join(UserRanches, Ranches.id == UserRanches.ranch_id)

    print(f"Initial Query: {str(query)}")

    if user.get('user_role') == 'admin':
        pass  # Admin can see all records
    elif user.get('user_role') in ['cheesemaker', 'rancher', 'vet']:
        query = query.filter(UserRanches.user_id == user.get('user_id'))
        print(f"Filtered Query for {user.get('user_role')}: {str(query)}")
    else:
        print(f"Forbidden Access for Role: {user.get('user_role')}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')

    if start_date and end_date:
        query = query.filter(Dairy_Milk.created_at >= start_date, Dairy_Milk.created_at <= end_date)
    elif start_date:
        query = query.filter(Dairy_Milk.created_at >= start_date)
    elif end_date:
        query = query.filter(Dairy_Milk.created_at <= end_date)

    if limit is not None:
        query = query.limit(limit)

    return query.all()

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


