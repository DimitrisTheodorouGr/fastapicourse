from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,DateTime, Float
from sqlalchemy.orm import relationship

class Ranches(Base):
    __tablename__ = 'ranches'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    # Define a relationship to UserRanches
    users = relationship('UserRanches', back_populates='ranch')
    stations = relationship('StationRanches', back_populates='ranch2')

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    # Define a relationship to UserRanches
    ranches = relationship('UserRanches', back_populates='user')


class UserRanches(Base):
    __tablename__ = 'user_ranches'
    user_id = Column(Integer, ForeignKey('users.id'),
                     primary_key=True)
    ranch_id = Column(Integer, ForeignKey('ranches.id'),
                      primary_key=True)

    # Create reverse relationships
    user = relationship('Users', back_populates='ranches')
    ranch = relationship('Ranches', back_populates='users')

class Animals(Base):
    __tablename__ =  'animals'
    id = Column(Integer, primary_key=True)
    ranch_id = Column(Integer, ForeignKey('ranches.id'))
    type = Column(String)
    tag = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class HealthRec(Base):
    __tablename__ = 'health_record'
    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animal.id'))
    head_injury = Column(Boolean, default=False)
    skin_condition = Column(Boolean, default=False)
    abscess = Column(Boolean, default=False)
    arthritis = Column(Boolean, default=False)
    swollen_hooves = Column(Boolean, default=False)
    mastitis = Column(Boolean, default=False)
    fibrosis = Column(Boolean, default=False)
    assymmetry = Column(Boolean, default=False)
    mammary_skin_conditions = Column(String)
    cmt_a = Column(Boolean, default=False)
    cmt_d = Column(Boolean, default=False)
    recorded_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Station(Base):
    __tablename__ = 'stations'
    id = Column(Integer, primary_key=True)
    station_name = Column(String)
    # Define a relationship to StationRanches
    ranch = relationship('StationRanches', back_populates='station')

class StationData(Base):
    __tablename__ = 'station_data'
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('stations.id'))
    timestamp = Column(DateTime)
    temperature = Column(Float)
    humidity = Column(Float)
    precipitation = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    solar_radiation = Column(Float)
    PM1 = Column(Float)
    PM2_5 = Column(Float)
    PM10 = Column(Float)
    CO2 =Column(Float)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
class StationRanches(Base):
    __tablename__ = 'station_ranches'
    station_id = Column(Integer, ForeignKey('stations.id'),
                     primary_key=True)
    ranch_id = Column(Integer, ForeignKey('ranches.id'),
                      primary_key=True)
    # Create reverse relationships
    station = relationship('Station', back_populates='ranch')
    ranch2 = relationship('Ranches', back_populates='stations')







