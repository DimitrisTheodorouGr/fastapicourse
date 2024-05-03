from app.database import SessionLocal
from app.models import Users, Ranches, UserRanches
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path
from typing import Union, Annotated
from sqlalchemy import text
from starlette import status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime


router = APIRouter(
    prefix='/ranch',
    tags=['Ranch']
)

class RanchRequest(BaseModel):
    name: str
    farm_id: str
    main_animal_species: str
    milked_animals: int
    milk_yield_per_year: float

class UserRanchRequest(BaseModel):
    ranch_id :int
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


# Example API endpoint
@router.get("/")
async def read_all_ranches_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher':
        return db.query(Ranches).join(UserRanches, UserRanches.ranch_id == Ranches.id).filter(UserRanches.user_id == user.get('user_id')).all()
    elif user.get('user_role') == 'admin':
        return db.query(Ranches).all()

@router.get('/{ranch_id}')
async def read_ranch_by_id(user:user_dependency, db: db_dependency, ranch_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    return db.query(Ranches).filter(Ranches.id == ranch_id).first()
@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_ranch(user: user_dependency, db: db_dependency, create_ranch_request: RanchRequest):

    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    create_ranch_model = Ranches(
        name=create_ranch_request.name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        farm_id=create_ranch_request.farm_id,
        main_animal_species=create_ranch_request.main_animal_species,
        milked_animals=create_ranch_request.milked_animals,
        milk_yield_per_year=create_ranch_request.milk_yield_per_year
    )
    db.add(create_ranch_model)
    db.commit()
@router.put("/{ranch_id}")
async def update_ranch(user: user_dependency,db: db_dependency, update_ranch_request: RanchRequest, ranch_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    ranch_model = db.query(Ranches).filter(Ranches.id == ranch_id).first()
    if ranch_model is None:
        raise HTTPException(status_code=404, detail='Ranch not found.')

    ranch_model.name = update_ranch_request.name
    ranch_model.farm_id = update_ranch_request.farm_id
    ranch_model.main_animal_species = update_ranch_request.main_animal_species
    ranch_model.milked_animals = update_ranch_request.milked_animals
    ranch_model.milk_yield_per_year = update_ranch_request.milk_yield_per_year
    ranch_model.updated_at = datetime.now()

    db.add(ranch_model)
    db.commit()

@router.delete("/{ranch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ranch(user:user_dependency,db: db_dependency, ranch_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    ranch_model = db.query(Ranches).filter(Ranches.id == ranch_id).first()
    if ranch_model is None:
        raise HTTPException(status_code=404, detail='User not found.')

    db.query(Ranches).filter(Ranches.id == ranch_id).delete()
    db.commit()
@router.post('/associate/{ranch_id}', status_code=status.HTTP_201_CREATED)
async def associate_ranch(user:user_dependency,db: db_dependency, create_user_ranch_request: UserRanchRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    ranch_model = db.query(UserRanches).filter(UserRanches.ranch_id == create_user_ranch_request.ranch_id).first()
    if ranch_model is not None:
        return {'message': 'Ranch already associated with an other user'}
    create_user_ranch_model = UserRanches(
        user_id=user.get('user_id'),
        ranch_id=create_user_ranch_request.ranch_id
        )
    db.add(create_user_ranch_model)
    db.commit()
@router.delete("/associate/{ranch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disassociate_ranch_from_user(user:user_dependency, db: db_dependency, ranch_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    ranch_model = db.query(UserRanches).filter(UserRanches.ranch_id == ranch_id).filter(UserRanches.user_id==user.get('user_id')).first()
    if ranch_model is None:
        raise HTTPException(status_code=404, detail='Association not found.')

    db.query(UserRanches).filter(UserRanches.ranch_id == ranch_id).filter(UserRanches.user_id==user.get('user_id')).delete()
    db.commit()
