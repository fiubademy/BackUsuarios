from typing import Optional
from pydantic import EmailStr
from pydantic.main import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, CheckConstraint
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from baseService.DataBase import Base

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
    sub_expire: Optional[str]
    is_blocked: str
    user_type: str
    avatar: Optional[int]

class User(Base):
    __tablename__ = "users"
    user_id = Column(String(500), primary_key=True, nullable=False)
    username = Column(String(100), nullable=False)
    email = Column(String(500), nullable=False, unique=True)
    password = Column(String(100))
    latitude = Column(Float, nullable = True)
    longitude = Column(Float, nullable = True)
    sub_level = Column(Integer, nullable=True)
    is_blocked = Column(String(5), nullable=False)
    user_type = Column(String(20), nullable=False)
    is_federated = Column(String(5))
    avatar = Column(Integer)
    __table_args__ = (
        CheckConstraint("NOT(password IS NULL AND is_federated != 'Y')"),
        CheckConstraint("NOT(password IS NOT NULL AND is_federated = 'Y')")
    )

    def __str__(self):
        return self.username

class TokensForUsers(Base):
    __tablename__ = "tokens_for_users"
    user_id = Column(String(500), primary_key = True, nullable = False)
    token = Column(String, primary_key = True, nullable = False)
    expiration_date = Column(DateTime, nullable = False)

    def __str__(self):
        return self.token


class RelationGoogleAndUser(Base):
    __tablename__ = "relations_google_and_users"
    id_google = Column(String, primary_key = True, nullable = False)
    user_id = Column(String(500), nullable = False)

    def __str__(self):
        return self.user_id


class PremiumSubsPayments(Base):
    __tablename__ = "premium_subs_payments"
    user_id = Column(String, primary_key = True, nullable = False)
    expiration_date = Column(DateTime, primary_key = True, nullable = False)


class StandardSubPayments(Base):
    __tablename__ = "standard_subs_payments"
    user_id = Column(String, primary_key = True, nullable = False)
    expiration_date = Column(DateTime, primary_key = True, nullable = False)