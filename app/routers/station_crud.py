from app.database import SessionLocal
from app.models import Users, Station, StationData, StationRanches,Ranches,UserRanches
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path, Query
from typing import Annotated,Optional
from starlette import status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime,date
from geoalchemy2 import WKTElement


router = APIRouter(
    prefix='/station',
    tags=['Station']
)
class StationRequest(BaseModel):
    station_name: str
    latitude: float
    longitude: float
class StationDataRequest(BaseModel):
    station_id: int
    timestamp: datetime
    temperature: float
    humidity: float
    precipitation: float
    pressure: float
    wind_speed: float
    wind_direction: float
    solar_radiation: float
    PM1: float
    PM2_5: float
    PM10: float
    CO2: float
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/' , status_code=status.HTTP_200_OK)
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
@router.get('/location/' , status_code=status.HTTP_200_OK)
def get_location(user:user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    stations = db.query(Station).join(StationRanches, Station.id == StationRanches.station_id)\
            .join(UserRanches, StationRanches.ranch_id == UserRanches.ranch_id)\
            .filter(UserRanches.user_id == user.get('user_id'))\
            .distinct().all()
    if stations is None:
        raise HTTPException(status_code=404, detail="Stations not found")
    # Building the GeoJSON object

    return {
      "type": "FeatureCollection",
      "features": [{
            "type": "Feature",
            "geometry": station.location_geojson(),
            "properties": {
                "id": station.id,
                "name": station.station_name
            }
        } for station in stations]}
@router.post('/', status_code=status.HTTP_201_CREATED)
def create_station(user:user_dependency, db: db_dependency, create_station_request: StationRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    # Create a WKT point string from latitude and longitude
    wkt_point = f'POINT({create_station_request.latitude} {create_station_request.longitude})'
    create_station_model = Station(
        station_name=create_station_request.station_name,
        location=WKTElement(wkt_point, srid=4326)
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

    wkt_point = f'POINT({edit_station_request.latitude} {edit_station_request.longitude})'
    edit_station_model.station_name = edit_station_request.station_name
    edit_station_model.updated_at = datetime.now()
    edit_station_model.location = WKTElement(wkt_point, srid=4326)
    db.add(edit_station_model)
    db.commit()

@router.get('/data')
def get_station_data_by_station(user:user_dependency, db: db_dependency, station_id: int = Query(ge=0),
                                limit: Optional[int] = Query(50, title="Max number of data returned", ge=0),
                                start_date: Optional[date] = Query(None, title="Start date of the range"),
                                end_date: Optional[date] = Query(None, title="End date of the range")):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    query = db.query(StationData).filter(StationData.station_id == station_id)
    if start_date and end_date:
        query = query.filter(StationData.timestamp >= start_date, StationData.timestamp <= end_date)
    elif start_date:
        query = query.filter(StationData.timestamp >= start_date)
    elif end_date:
        query = query.filter(StationData.timestamp <= end_date)


    if limit is not None:  # Ensuring the limit is considered only if provided
        query = query.limit(limit)
    return query.all()
@router.post('/data')
async def create_station_data(user: user_dependency, db: db_dependency, station_data_request:StationDataRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    station_data_model = StationData(
        station_id=station_data_request.station_id,
        timestamp=station_data_request.timestamp,
        temperature=station_data_request.temperature,
        humidity=station_data_request.pressure,
        precipitation=station_data_request.precipitation,
        pressure=station_data_request.pressure,
        wind_speed=station_data_request.wind_speed,
        wind_direction=station_data_request.wind_direction,
        solar_radiation=station_data_request.solar_radiation,
        PM1=station_data_request.PM1,
        PM2_5=station_data_request.PM2_5,
        PM10=station_data_request.PM10,
        CO2=station_data_request.CO2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        )
    db.add(station_data_model)
    db.commit()
@router.delete('/data/{data_id}')
def delete_data_by_id(user: user_dependency, db: db_dependency, data_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    station_data_query = db.query(StationData).filter(StationData.id == data_id).first()
    if station_data_query is None:
        raise HTTPException(status_code=404, detail='Data Not Found')
    db.delete(station_data_query)
    db.commit()
@router.get("/data/last")
def get_last_station_data(user: user_dependency,
                              db: db_dependency,
                              station_id: int = Query(ge=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    query = db.query(StationData).filter(StationData.station_id == station_id).order_by(
            StationData.timestamp.desc()).first()

    if query is None:
        raise HTTPException(status_code=404, detail='Data not found')

    return query


