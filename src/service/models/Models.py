from typing import Optional
from pydantic import EmailStr
from pydantic.main import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from src.service.DataBase import Base

class UserRequest(BaseModel):
    username: str
    user_id: str
    email: EmailStr

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    latitude: Optional[float]
    longitude: Optional[float]
    sub_level: Optional[int]

class User(Base):
    __tablename__ = "users"
    user_id = Column(String(500), primary_key=True, nullable=False)
    username = Column(String(100), nullable=False)
    email = Column(String(500), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    latitude = Column(Float, nullable = True)
    longitude = Column(Float, nullable = True)
    sub_level = Column(Integer, nullable=True)

    def __str__(self):
        return self.username

class TokensForUsers(Base):
    __tablename__ = "tokens_for_users"
    user_id = Column(String(500), primary_key = True, nullable = False)
    token = Column(String, primary_key = True, nullable = False)
    expiration_date = Column(DateTime, nullable = False)

    def __str__(self):
        return self.token