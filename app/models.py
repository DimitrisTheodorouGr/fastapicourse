from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,DateTime
from sqlalchemy.orm import relationship

class Ranches(Base):
    __tablename__ = 'ranches'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    # Define a relationship to UserRanches
    users = relationship('UserRanches', back_populates='ranch')

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
                     primary_key=True)  # assuming there is a users table with an id column
    ranch_id = Column(Integer, ForeignKey('ranches.id'),
                      primary_key=True)  # assuming there is a ranches table with an id column

    # Create reverse relationships
    user = relationship('Users', back_populates='ranches')
    ranch = relationship('Ranches', back_populates='users')

