from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,DateTime, Float
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
import json
class Ranches(Base):
    __tablename__ = 'ranches'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    farm_id = Column(String)
    main_animal_species = Column(String)
    milked_animals = Column(Integer)
    milk_yield_per_year = Column(Float)
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
    age = Column(Integer)
    status = Column(Boolean)  # 0 = Dead, 1 = Alive

class HealthRec(Base):
    __tablename__ = 'health_record'
    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animals.id'))
    head_injury = Column(Boolean, default=False)
    skin_conditions = Column(Boolean, default=False)
    abscess = Column(Boolean, default=False)
    arthritis = Column(Boolean, default=False)
    swollen_hooves = Column(Boolean, default=False)
    mastitis = Column(Boolean, default=False)
    fibrosis = Column(Boolean, default=False)
    asymmetry = Column(Boolean, default=False)
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
    location = Column(Geometry('POINT', srid=4326))

    def location_geojson(self):
        # Convert the Geometry to a Shapely geometry object and then to GeoJSON
        shape = to_shape(self.location)
        return json.loads(json.dumps(shape.__geo_interface__))

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
    CO2 = Column(Float, nullable=True)
    AQI = Column(Float, nullable=True)
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

class WellIndex(Base):
    __tablename__ = 'wellbeing_index'
    id = Column(Integer, primary_key=True)
    ranch_id = Column(Integer, ForeignKey('ranches.id'))
    index_value = Column(Float)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Dairy_Milk(Base):
    __tablename__ = 'dairy_milk'
    id = Column(Integer, primary_key=True)
    ranch_id = Column(Integer, ForeignKey('ranches.id'))
    milk_quality = Column(Float)
    milk_quantity = Column(Float)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Collars(Base):
    __tablename__ = 'collars'
    id = Column(Integer, primary_key=True)
    dev_eui = Column(String)
    animal_id = Column(Integer, ForeignKey('animals.id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class CollarGPSData(Base):
    __tablename__ = 'collar_gps_data'
    id = Column(Integer, primary_key=True)
    collar_id = Column(Integer, ForeignKey('collars.id'))
    coordinates = Column(Geometry('POINT', srid=4326))
    temperature = Column(Float)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    timestamp = Column(DateTime)
    def coordinates_geojson(self):
        # Convert the Geometry to a Shapely geometry object and then to GeoJSON
        shape = to_shape(self.coordinates)
        return json.loads(json.dumps(shape.__geo_interface__))


