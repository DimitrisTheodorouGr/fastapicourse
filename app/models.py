from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,DateTime


class Ranches(Base):
    __tablename__ = 'ranches'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
