from app.database import SessionLocal
from app.models import Users,Ranches,UserRanches,WellIndex
from .auth import get_current_user
from fastapi import Depends, APIRouter, HTTPException, Path, Query
from typing import Annotated,Optional,List
from starlette import status
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from datetime import datetime,date


router = APIRouter(
    prefix='/wellindex',
    tags=['WellIndex']
)

class WellIndexInfoResponse(BaseModel):
    ranch_name: str
    index_value: float
    created_at: datetime
    updated_at: datetime

class WellIndexRequest(BaseModel):
    ranch_id: int = Field(gt=0)
    index_value: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Dependancy connection
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/' ,response_model= List[WellIndexInfoResponse], status_code=status.HTTP_200_OK)
def get_wellindex_list_based_on_role(user:user_dependency, db: db_dependency,
                                    limit: Optional[int] = Query(50, title="Max number of data returned", ge=0),
                                    start_date: Optional[date] = Query(None, title="Start date of the range"),
                                    end_date: Optional[date] = Query(None, title="End date of the range")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')

    query = db.query(
        UserRanches.user_id,
        Ranches.name.label('ranch_name'),
        WellIndex.index_value.label('index_value'),
        WellIndex.created_at.label('created_at'),
        WellIndex.updated_at.label('updated_at')
    ).join(Ranches, UserRanches.ranch_id == Ranches.id) \
        .join(WellIndex, Ranches.id == WellIndex.ranch_id)

    if user.get('user_role') in ['rancher', 'vet']:
        query = query.filter(UserRanches.user_id == user.get('user_id'))
    elif user.get('user_role') == 'admin':
        pass  # No additional filtering needed for admin
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')

    if start_date and end_date:
        query = query.filter(WellIndex.created_at >= start_date, WellIndex.created_at <= end_date)
    elif start_date:
        query = query.filter(WellIndex.created_at >= start_date)
    elif end_date:
        query = query.filter(WellIndex.created_at <= end_date)

    if limit is not None:  # Ensuring the limit is considered only if provided
        query = query.limit(limit)

    return query.all()
@router.get('/last/{ranch_id}', status_code=status.HTTP_200_OK)
def get_wellindex_last(user: user_dependency, db: db_dependency, ranch_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    query = db.query(WellIndex).filter(WellIndex.ranch_id == ranch_id).order_by(
        WellIndex.created_at.desc()).first()
    if query is None:
        raise HTTPException(status_code=404, detail='Data not found')

    return query
@router.post('/' , status_code=status.HTTP_201_CREATED)
async def create_wellindex(user: user_dependency, db:db_dependency, wellindexrequest:WellIndexRequest):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    wellindex_model = WellIndex(
        ranch_id= wellindexrequest.ranch_id,
        index_value = wellindexrequest.index_value,
        created_at = datetime.now(),
        updated_at = datetime.now(),
    )

    db.add(wellindex_model)
    db.commit()

@router.put('/{wellindex_id}' , status_code=status.HTTP_204_NO_CONTENT)
async def update_wellindex(user: user_dependency, db:db_dependency, update_wellindex_request:WellIndexRequest, wellindex_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    wellindex_model = db.query(WellIndex).filter(WellIndex.id == wellindex_id).first()
    if wellindex_model is None:
        raise HTTPException(status_code=404, detail='Wellbeing index not found')
    wellindex_model.index_value = update_wellindex_request.index_value
    wellindex_model.ranch_id = update_wellindex_request.ranch_id
    wellindex_model.updated_at = datetime.now()

    db.add(wellindex_model)
    db.commit()

@router.delete("/{wellindex_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wellindex(user:user_dependency,db: db_dependency, wellindex_id: int= Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    wellindex_query = db.query(WellIndex).filter(WellIndex.id == wellindex_id).first
    if wellindex_query is None:
        raise HTTPException(status_code=404, detail='Wellbeing index not found.')

    db.query(WellIndex).filter(WellIndex.id == wellindex_id).delete()
    db.commit()


