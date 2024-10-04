from starlette import status
from .auth import get_current_user
from app.database import SessionLocal
from app.models import Users, UserRanches, Ranches,Station,StationRanches
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Path ,Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

router = APIRouter(
    prefix="/admin",
    tags=['Admin']
)

class StationInfoResponse(BaseModel):
    ranch_id: int
    ranch_name: str
    station_id: int
    station_name: str
class StationRanchRequest(BaseModel):
    ranch_id: int
    station_id: int
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
@router.get('/getusersinfo')
async def get_users_info(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        query = db.query(Users).all()
        return [{"id": data.id, "username:": data.username, "email:": data.email, "role:": data.role, "created_at": data.created_at, "updated_at": data.updated_at} for data in query]
@router.put('/change-user-role')
async def change_user_role(user: user_dependency, db: db_dependency, user_role: str, username: str):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        user_model = db.query(Users).filter(Users.username == username).first()
        if user_model is None:
            return HTTPException(status_code=404, detail='No User found')
        user_model.role = user_role
        user_model.updated_at = datetime.now()
        db.add(user_model)
        db.commit()

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

@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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

@router.delete("/station/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(user: user_dependency, db: db_dependency, station_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        station_model = db.query(station_id).filter(Station.id == station_id).first()
        if station_model is None:
                raise HTTPException(status_code=404, detail='Station not found.')

        db.query(Station).filter(Station.id == station_id).delete()
        db.commit()
    else:
        return {'message': 'Only admins can delete'}
@router.get("/stations-associations/", response_model= List[StationInfoResponse])
def read_stations_ranches_associations(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        results = db.query(Ranches.id.label('ranch_id'), Ranches.name.label('ranch_name'),
                               Station.id.label('station_id'), Station.station_name).\
                        join(StationRanches, Ranches.id == StationRanches.ranch_id).\
                        join(Station, Station.id == StationRanches.station_id).all()
        return results
@router.post("/stations-associations/", status_code=status.HTTP_201_CREATED)
def create_stations_ranches_associations(db: db_dependency,user: user_dependency, station_ranch_request:StationRanchRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        station_ranch_model = StationRanches(**station_ranch_request.dict())
        db.add(station_ranch_model)
        db.commit()
@router.delete("/stations-associations/", status_code=status.HTTP_204_NO_CONTENT)
def create_stations_ranches_associations(db: db_dependency,user: user_dependency, station_id: int, ranch_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    if user.get('user_role') == 'admin':
        station_ranch_model = db.query(StationRanches).filter(StationRanches.station_id == station_id,
                                                  StationRanches.ranch_id == ranch_id).first()
        if not station_ranch_model:
            raise HTTPException(status_code=404, detail="Station Ranch Association not found")

        db.delete(station_ranch_model)
        db.commit()