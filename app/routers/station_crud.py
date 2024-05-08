from app.database import SessionLocal
from app.models import Users, Station, StationData, StationRanches,Ranches,UserRanches
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path
from typing import Annotated
from starlette import status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime


router = APIRouter(
    prefix='/station',
    tags=['Station']
)
class StationRequest(BaseModel):
    station_name: str
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/')
def get_station_list_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher' or user.get('user_role') == 'vet':
        query = (
            db.query(Station.station_name, Station.id)
            .join(StationRanches, Station.id == StationRanches.station_id)
            .join(UserRanches, StationRanches.ranch_id == UserRanches.ranch_id)
            .filter(UserRanches.user_id == user.get('user_id'))
            .distinct()
        )
        # Execute the query
        stations = query.all()
        return [{"station_name": station.station_name, "station_id": station.id} for station in stations]

    elif user.get('user_role') == 'admin':
        return db.query(Station).all()
@router.post('/', status_code=status.HTTP_201_CREATED)
def create_station(user:user_dependency, db: db_dependency, create_station_request: StationRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    create_station_model = Station(
        name=create_station_request.name,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(create_station_model)
    db.commit()

@router.put('/{station_id}', status_code=status.HTTP_204_NO_CONTENT)
def update_station_info( user: user_dependency, db: db_dependency, edit_station_request: StationRequest,station_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    edit_station_model = db.query(Station).filter(Station.id == station_id).first()
    if edit_station_model is None:
        return HTTPException(status_code=404, detail='Station not fount')
    edit_station_model.name = edit_station_request.station_name
    edit_station_model.updated_at = datetime.now()
    db.add(edit_station_model)
    db.commit()