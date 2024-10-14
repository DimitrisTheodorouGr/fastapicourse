from app.database import SessionLocal
from app.models import Ranches,UserRanches,Animals,Collars,CollarGPSData
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path, Query, UploadFile, File, Form, status
from typing import Annotated,Optional,List
from starlette import status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from datetime import datetime,date
from geoalchemy2 import WKTElement
from shapely.geometry import Point,LineString
import xml.etree.ElementTree as ET
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
    temperature: float
    battery_percentage: float
    altitude: float
    humidity: float
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
@router.get('/all_collars' ,status_code=status.HTTP_200_OK)
def get_all_collar_list(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher' or user.get('user_role') == 'vet':
        raise HTTPException(status_code=403, detail='Forbidden')
    elif user.get('user_role') == 'admin':
        return db.query(Collars).all()
@router.get('/without_collar' , response_model=List[WithoutCollarInfoResponse],status_code=status.HTTP_200_OK)
def get_animal_list_without_collar_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher' or user.get('user_role') == 'vet':
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
    elif user.get('user_role') == 'admin':
        results = db.query(
            Animals.id.label('animal_id'),
            Animals.type.label('animal_type'),
            Animals.tag.label('animal_tag'),
            Ranches.name.label('ranch_name')
        ).join(Ranches, Ranches.id == Animals.ranch_id) \
            .join(UserRanches, UserRanches.ranch_id == Ranches.id) \
            .outerjoin(Collars, Animals.id == Collars.animal_id) \
            .filter(Collars.id.is_(None)) \
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
        battery_percentage=create_collar_data_request.battery_percentage,
        altitude=create_collar_data_request.altitude,
        humidity=create_collar_data_request.humidity,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        timestamp=create_collar_data_request.timestamp,
        )

    db.add(collar_data_model)
    db.commit()
@router.get('/data/', status_code=status.HTTP_200_OK)
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

    if start_date and end_date:
        query = query.filter(CollarGPSData.timestamp >= start_date, CollarGPSData.timestamp <= end_date)
    elif start_date:
        query = query.filter(CollarGPSData.timestamp >= start_date)
    elif end_date:
        query = query.filter(CollarGPSData.timestamp <= end_date)

    if limit is not None:
        query = query.limit(limit)
    collar_data = query.all()

    if not collar_data:
        raise HTTPException(status_code=404, detail="No data found within the specified range")

    # Use Shapely Point for individual locations
    features = []
    for data in collar_data:
        point = Point(data.coordinates_geojson()['coordinates'])
        features.append({
            "type": "Feature",
            "geometry": point.__geo_interface__,
            "properties": {
                "id": data.id,
                "temperature": data.temperature,
                "battery_percentage": data.battery_percentage,
                "altitude": data.altitude,
                "humidity": data.humidity,
                "timestamp": data.timestamp
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
@router.get('/data/values_only',status_code=status.HTTP_200_OK)
async def get_collar_data_values_only(user: user_dependency, db: db_dependency,
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
    return [{   "id": data.id,
                "temperature": data.temperature,
                "battery_percentage": data.battery_percentage,
                "altitude": data.altitude,
                "humidity": data.humidity,
                "timestamp": data.timestamp
            } for data in collar_data]
@router.get("/data/battery")
def get_last_battery_data(user: user_dependency, db: db_dependency, collar_id: int = Query(ge=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    query = db.query(CollarGPSData).filter(CollarGPSData.collar_id == collar_id).order_by(
        CollarGPSData.timestamp.desc()).first()

    if query is None:
        raise HTTPException(status_code=404, detail='Data not found')

    return {"battery": query.battery_percentage}

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
# Endpoint to upload XML file and process it with collar_id
@router.post("/data/upload-xml", status_code=status.HTTP_201_CREATED)
async def upload_xml_file(
    user: user_dependency,
    db: db_dependency,
    file: UploadFile = File(...),
    collar_id: int = Form(...)
):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    if not file.filename.endswith(".xml"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an .xml file.")

    # Read the uploaded XML file content
    xml_content = await file.read()

    # Parse the XML content
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        raise HTTPException(status_code=400, detail="Invalid XML file structure.")

    # Namespace for XML if needed (e.g., for KML-like structures)
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}  # Adjust the namespace if necessary
    placemarks = []

    # Iterate through each Placemark or other relevant XML elements and collect data
    for placemark in root.findall(".//kml:Placemark", namespace):  # Adjust based on your XML structure
        coordinates = placemark.find(".//kml:Point/kml:coordinates", namespace)
        when = placemark.find(".//kml:TimeStamp/kml:when", namespace)

        if coordinates is not None and when is not None:
            coord_text = coordinates.text.strip()
            longitude, latitude, altitude = map(float, coord_text.split(","))

            # Extract the timestamp from the XML
            timestamp = when.text

            # Create the WKT point string from the coordinates
            wkt_point = f'POINT({latitude} {longitude})'

            # Prepare the collar data model to be inserted into the database
            collar_data_model = CollarGPSData(
                collar_id=collar_id,
                coordinates=WKTElement(wkt_point, srid=4326),
                temperature=0,  # Placeholder, adjust as needed
                battery_percentage=0,  # Placeholder, adjust as needed
                altitude=altitude,
                humidity=0,  # Placeholder, adjust as needed
                created_at=datetime.now(),
                updated_at=datetime.now(),
                timestamp=timestamp,
            )

            db.add(collar_data_model)

    db.commit()
    return {"message": f"Collar GPS data uploaded successfully for collar_id {collar_id}"}