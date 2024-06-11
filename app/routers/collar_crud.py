from app.database import SessionLocal
from app.models import Ranches,UserRanches,Animals,Collars,CollarGPSData
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path, Query
from typing import Annotated,Optional,List
from starlette import status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from datetime import datetime,date
from geoalchemy2 import WKTElement
from shapely.geometry import LineString
import json


router = APIRouter(
    prefix='/collar',
    tags=['Collar']
)
class CollarInfoResponse(BaseModel):
    animal_tag: str
    ranch_name: str
    animal_id: int
    collar_id: int
    collar_dev_eui: str
    created_at: datetime
    updated_at: datetime
class WithoutCollarInfoResponse(BaseModel):
    animal_id: int
    animal_tag: str
    ranch_name: str
    animal_type: str
class CollarRequest(BaseModel):
    animal_id: int = Field(gt=0)
    collar_dev_eui: str

class CollarDataRequest(BaseModel):
    collar_id: int = Field(gt=0)
    latitude: float
    longitude: float
    temperature:float
    timestamp: datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]



@router.get('/' , response_model=List[CollarInfoResponse],status_code=status.HTTP_200_OK)
def get_collar_list_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher' or user.get('user_role') == 'vet':

        return db.query(Animals.tag.label('animal_tag'),Ranches.name.label('ranch_name'),Collars.animal_id.label('animal_id'), Collars.id.label('collar_id'),
                         Collars.dev_eui.label('collar_dev_eui'), Collars.created_at.label('created_at'), Collars.updated_at.label('updated_at'))\
                        .select_from(UserRanches) \
                        .join(Ranches, UserRanches.ranch_id == Ranches.id) \
                        .join(Animals, Ranches.id == Animals.ranch_id) \
                        .join(Collars, Animals.id == Collars.animal_id) \
                        .filter(UserRanches.user_id == user.get('user_id')).all()

    elif user.get('user_role') == 'admin':
        return db.query(Animals.tag.label('animal_tag'),Ranches.name.label('ranch_name'),Collars.animal_id.label('animal_id'), Collars.id.label('collar_id'),
                         Collars.dev_eui.label('collar_dev_eui'), Collars.created_at.label('created_at'), Collars.updated_at.label('updated_at'))\
                        .select_from(UserRanches) \
                        .join(Ranches, UserRanches.ranch_id == Ranches.id) \
                        .join(Animals, Ranches.id == Animals.ranch_id) \
                        .join(Collars, Animals.id == Collars.animal_id).all()

@router.get('/without_collar' , response_model=List[WithoutCollarInfoResponse],status_code=status.HTTP_200_OK)
def get_animal_list_without_collar_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    results = db.query(
        Animals.id.label('animal_id'),
        Animals.type.label('animal_type'),
        Animals.tag.label('animal_tag'),
        Ranches.name.label('ranch_name')
    ).join(Ranches, Ranches.id == Animals.ranch_id) \
        .join(UserRanches, UserRanches.ranch_id == Ranches.id) \
        .outerjoin(Collars, Animals.id == Collars.animal_id) \
        .filter(UserRanches.user_id == user.get('user_id'), Collars.id.is_(None)) \
        .all()

    if not results:
        raise HTTPException(status_code=404, detail="No animals without collars found for this user's ranches")

    return results

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_collar(user: user_dependency, db: db_dependency, create_collar_request: CollarRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    collar_model = Collars(
        dev_eui=create_collar_request.collar_dev_eui,
        animal_id=create_collar_request.animal_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
        )
    db.add(collar_model)
    db.commit()

@router.put('/{collar_id}', status_code=status.HTTP_204_NO_CONTENT)
async def edit_collar(user: user_dependency, db: db_dependency, edit_collar_request: CollarRequest, collar_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    collar_model = db.query(Collars).filter(Collars.id == collar_id).first()
    if collar_model is None:
        return HTTPException(status_code=404, detail='Collar not fount')

    collar_model.dev_eui = edit_collar_request.collar_dev_eui,
    collar_model.animal_id = edit_collar_request.animal_id,
    collar_model.updated_at = datetime.now()

    db.add(collar_model)
    db.commit()
@router.delete('/{collar_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_collar(user: user_dependency, db: db_dependency, collar_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    collar_model = db.query(Collars).filter(Collars.id == collar_id).first()
    if collar_model is None:
        return HTTPException(status_code=404, detail='Collar not fount')
    db.delete(collar_model)
    db.commit()
@router.post('/data/', status_code=status.HTTP_201_CREATED)
async def create_collar_data(user: user_dependency, db: db_dependency, create_collar_data_request: CollarDataRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
        # Create a WKT point string from latitude and longitude
    wkt_point = f'POINT({create_collar_data_request.latitude} {create_collar_data_request.longitude})'
    collar_data_model = CollarGPSData(

        collar_id=create_collar_data_request.collar_id,
        coordinates=WKTElement(wkt_point, srid=4326) ,
        temperature=create_collar_data_request.temperature,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        timestamp=create_collar_data_request.timestamp,
        )

    db.add(collar_data_model)
    db.commit()
@router.get('/data/',status_code=status.HTTP_200_OK)
async def get_collar_data_geojson(user: user_dependency, db: db_dependency,
                                  collar_id: int,
                                  limit: Optional[int] = Query(50, title="Max number of data returned", ge=0),
                                  start_date: Optional[date] = Query(None, title="Start date of the range"),
                                  end_date: Optional[date] = Query(None, title="End date of the range")):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    query = db.query(CollarGPSData).filter(CollarGPSData.collar_id == collar_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Gps data not found")
    # Building the GeoJSON object

    if start_date and end_date:
        query = query.filter(CollarGPSData.timestamp >= start_date, CollarGPSData.timestamp <= end_date)
    elif start_date:
        query = query.filter(CollarGPSData.timestamp >= start_date)
    elif end_date:
        query = query.filter(CollarGPSData.timestamp <= end_date)


    if limit is not None:  # Ensuring the limit is considered only if provided
        query = query.limit(limit)
    collar_data = query.all()
    return {
      "type": "FeatureCollection",
      "features": [{
            "type": "Feature",
            "geometry": data.coordinates_geojson(),
            "properties": {
                "id": data.id,
                "temperature": data.temperature,
                "timestamp": data.timestamp
            }
        } for data in collar_data]}
@router.get('/data/route', status_code=status.HTTP_200_OK)
async def get_collar_data_route_geojson(user: user_dependency, db: db_dependency,
                                  collar_id: int,
                                  limit: Optional[int] = Query(50, title="Max number of data returned", ge=0),
                                  start_date: Optional[date] = Query(None, title="Start date of the range"),
                                  end_date: Optional[date] = Query(None, title="End date of the range")):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    query = db.query(CollarGPSData).filter(CollarGPSData.collar_id == collar_id)
    if query is None:
        raise HTTPException(status_code=404, detail="Gps data not found")

    if start_date and end_date:
        query = query.filter(CollarGPSData.timestamp >= start_date, CollarGPSData.timestamp <= end_date)
    elif start_date:
        query = query.filter(CollarGPSData.timestamp >= start_date)
    elif end_date:
        query = query.filter(CollarGPSData.timestamp <= end_date)

    if limit is not None:
        query = query.limit(limit)
    collar_data = query.all()

    from shapely.geometry import LineString

    line = LineString([data.coordinates_geojson()['coordinates'] for data in collar_data])

    return {
      "type": "FeatureCollection",
      "features": [{
            "type": "Feature",
            "geometry": line.__geo_interface__,
            "properties": {
                "collar_id": collar_id
            }
        }]
    }