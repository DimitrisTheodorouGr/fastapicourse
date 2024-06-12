from app.database import SessionLocal
from app.models import Users,Ranches,UserRanches,Animals,HealthRec
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path, Query
from typing import Annotated,Optional,List
from starlette import status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from datetime import datetime,date


router = APIRouter(
    prefix='/animal',
    tags=['Animal']
)
class AnimalInfoResponse(BaseModel):
    ranch_name: str
    animal_id: int
    animal_tag: str
    animal_age: int
    animal_type: str
    animal_status: bool
    created_at: datetime
    updated_at: datetime
class AnimalRequest(BaseModel):
    ranch_id: int = Field(gt=0)
    tag: str = Field(maxlength=12)
    status: bool
    age: int = Field(gt=0)
    type: str

class HealthRequest(BaseModel):
    animal_id: int = Field(gt=0)
    head_injury: bool = Field(default=False)
    skin_condition: bool =Field(default=False)
    abscess: bool=Field(default=False)
    arthritis : bool=Field(default=False)
    swollen_hooves : bool=Field(default=False)
    mastitis: bool=Field(default=False)
    fibrosis: bool=Field(default=False)
    assymmetry : bool=Field(default=False)
    mammary_skin_conditions :str
    cmt_a  : bool=Field(default=False)
    cmt_d : bool=Field(default=False)
    recorded_at: datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/' ,response_model= List[AnimalInfoResponse], status_code=status.HTTP_200_OK)
def get_animal_list_based_on_role(user:user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    elif user.get('user_role') == 'rancher' or user.get('user_role') == 'vet':

        return db.query(UserRanches.user_id, Ranches.name.label('ranch_name'), Animals.type.label('animal_type'), Animals.tag.label('animal_tag'),Animals.id.label('animal_id'),
                         Animals.age.label('animal_age'),Animals.status.label('animal_status'), Animals.created_at.label('created_at'), Animals.updated_at.label('updated_at')) \
            .join(Ranches, UserRanches.ranch_id == Ranches.id) \
            .join(Animals, Ranches.id == Animals.ranch_id) \
            .filter(UserRanches.user_id == user.get('user_id')).all()
    elif user.get('user_role') == 'admin':
        return db.query(UserRanches.user_id, Ranches.name.label('ranch_name'), Animals.type.label('animal_type'), Animals.tag.label('animal_tag'),Animals.id.label('animal_id'),
                         Animals.age.label('animal_age'),Animals.status.label('animal_status'), Animals.created_at.label('created_at'), Animals.updated_at.label('updated_at')) \
                .join(Ranches, UserRanches.ranch_id == Ranches.id) \
                .join(Animals, Ranches.id == Animals.ranch_id).all()
@router.post('/' , status_code=status.HTTP_201_CREATED)
async def create_animal(user: user_dependency, db:db_dependency, animalrequest:AnimalRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    animal_model = Animals(
        ranch_id= animalrequest.ranch_id,
        type = animalrequest.type,
        tag =animalrequest.tag,
        created_at = datetime.now(),
        updated_at = datetime.now(),
        age =animalrequest.age,
        status = True  # 0 = Dead, 1 = Alive
    )
    db.add(animal_model)
    db.commit()
@router.put('/{animal_id}' , status_code=status.HTTP_204_NO_CONTENT)
async def update_animal(user: user_dependency, db:db_dependency, animaleditrequest:AnimalRequest, animal_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    animal_model = db.query(Animals).filter(Animals.id == animal_id).first()
    if animal_model is None:
        raise HTTPException(status_code=404, detail='Animal not found')
    animal_model.tag = animaleditrequest.tag
    animal_model.age = animaleditrequest.age
    animal_model.type = animaleditrequest.type
    animal_model.status = animaleditrequest.status
    animal_model.ranch_id = animaleditrequest.ranch_id
    animal_model.updated_at = datetime.now()

    db.add(animal_model)
    db.commit()
@router.delete('/{animal_id}' , status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(user: user_dependency, db:db_dependency, animal_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    animal_query = db.query(Animals).filter(Animals.id == animal_id).first()
    if animal_query is None:
        raise HTTPException(status_code=404, detail='Animal Not Found')
    db.delete(animal_query)
    db.commit()
@router.get('/healthrecord/', status_code=status.HTTP_200_OK)
async def get_health_record_by_animal_id(user: user_dependency, db: db_dependency, animal_id: int = Query(ge=0),
                                limit: Optional[int] = Query(50, title="Max number of data returned", ge=0),
                                start_date: Optional[date] = Query(None, title="Start date of the range"),
                                end_date: Optional[date] = Query(None, title="End date of the range")):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    query = db.query(HealthRec).filter(HealthRec.animal_id == animal_id)

    if start_date and end_date:
        query = query.filter(HealthRec.recorded_at >= start_date, HealthRec.recorded_at <= end_date)
    elif start_date:
        query = query.filter(HealthRec.recorded_at >= start_date)
    elif end_date:
        query = query.filter(HealthRec.recorded_at <= end_date)

    if limit is not None:  # Ensuring the limit is considered only if provided
        query = query.limit(limit)

    return query.all()
@router.post('/healthrecord', status_code=status.HTTP_201_CREATED)
async def create_health_record(user: user_dependency, db:db_dependency, health_request:HealthRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    health_rec_model = HealthRec(
        animal_id= health_request.animal_id,
        head_injury =health_request.head_injury ,
        skin_conditions = health_request.skin_condition,
        abscess = health_request.abscess,
        arthritis = health_request.arthritis,
        swollen_hooves = health_request.swollen_hooves,
        mastitis = health_request.mastitis,
        fibrosis = health_request.fibrosis,
        asymmetry = health_request.assymmetry,
        mammary_skin_conditions = health_request.mammary_skin_conditions,
        cmt_a = health_request.cmt_a,
        cmt_d = health_request.cmt_d,
        recorded_at = health_request.recorded_at,
        created_at = datetime.now(),
        updated_at = datetime.now(),
    )
    db.add(health_rec_model)
    db.commit()

@router.delete('/healthrecord/{record_id}' , status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_record(user: user_dependency, db:db_dependency, record_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    query = db.query(HealthRec).filter(HealthRec.id == record_id).first()
    if query is None:
        raise HTTPException(status_code=404, detail='Health Record Not Found')
    db.delete(query)
    db.commit()

