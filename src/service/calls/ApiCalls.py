from fastapi import status
from typing import List, Optional
from pydantic import EmailStr
from starlette.responses import JSONResponse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.sql import null
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from models.Models import UserRequest, UserResponse, User, TokensForUsers
import uuid
import hashlib

PER_PAGE = 5

router = APIRouter()
Session = None
session = None
engine = None

def set_engine(engine_rcvd):
    global engine
    global Session
    global session
    engine = engine_rcvd
    Session = sessionmaker(bind=engine)
    session = Session()

@router.get('/{page_num}', response_model = List[UserResponse], status_code=status.HTTP_200_OK)
async def getUsers(page_num: int, emailFilter: Optional[str] = '', usernameFilter: Optional[str] = ''):
    mensaje = []
    try:
        users = session.query(User).filter(User.email.like("%"+emailFilter+"%")).filter(User.username.like("%"+usernameFilter+"%")).limit(PER_PAGE).offset((page_num-1) * PER_PAGE)
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content= 'No users found in page ' + str(page_num) + ' in the database.')
    if (users.count() == 0):
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content= 'No users found in page ' + str(page_num) + ' in the database.')
    for user in users:
        mensaje.append ({'user_id':user.user_id, 'username':user.username, 'email':user.email, 'latitude':user.latitude, 'longitude': user.longitude, 'sub_level': user.sub_level})
    return mensaje

@router.get('/ID/{user_id}', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def getUser(user_id= ''):
    if user_id == '':
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content='Cannot search for null users.')
    if session.query(User.username, User.user_id, User.email).filter(User.user_id == user_id).count() == 0:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found.')
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found.')
    return{'user_id':user.user_id, 'username':user.username, 'email':user.email, 'latitude':user.latitude, 'longitude': user.longitude, 'sub_level': user.sub_level}

@router.get('/get_token/{user_id}', response_model=str, status_code=status.HTTP_200_OK)
async def getTokenForRecPasswd(user_id:str):

    token = str(uuid.uuid4())
    token_for_users = TokensForUsers(user_id=user_id, token=token, expiration_date = (datetime.now() + timedelta(days=1)))

    # Veo que el usuario exista en mi red de usuarios
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found.')
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found.')

    # Busco a ver si hay tokens existentes y los elimino.
    session.query(TokensForUsers).filter(TokensForUsers.user_id == user_id).delete()

    # Genero el nuevo token y lo devuevo
    session.add(token_for_users)
    session.commit()
    return token

@router.post('/', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def createUser(username: str, email: EmailStr, password: str):
    user_id = str(uuid.uuid4())
    newUser = User(user_id=user_id, 
                    username=username, 
                    email=email, 
                    password=(hashlib.sha256(password.encode())).hexdigest(),
                    latitude = null(),
                    longitude = null(),
                    sub_level = null())
    session.add(newUser)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content='Email ' + email + ' already registered as a user.')
    return {'user_id':newUser.user_id, 'username':newUser.username, 'email':newUser.email, 'latitude':newUser.latitude, 'longitude': newUser.longitude, 'sub_level': newUser.sub_level}

@router.delete('/{user_id}', status_code=status.HTTP_202_ACCEPTED)
async def deleteUser(user_id):
    try:
        session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found and will not be deleted.')
    session.query(User).filter(User.user_id == user_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content='User ' + user_id + ' was deleted succesfully.')

@router.patch('/{user_id}')
async def patchUser(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found and will not be patched.')
    if(email is not None):
        user.email = email
    if(username is not None):
        user.username = username
    session.add(user)
    session.commit()
    return {'user_id':user.user_id, 'username':user.username, 'email':user.email, 'latitude':user.latitude, 'longitude': user.longitude, 'sub_level': user.sub_level}


@router.patch('/changePassword/{user_id}')
async def changePassword(user_id: str, oldPassword: str, newPassword: str):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'User ' + user_id + ' was not found in the database')
    if(hashlib.sha256(oldPassword.encode()).hexdigest() != user.password):
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Your old password is not correct.')
    user.password = hashlib.sha256(newPassword.encode()).hexdigest()
    session.add(user)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = (user.username +'\'s password has been correctly changed.'))
    

@router.patch('/recoverPassword/{user_id}')
async def recoverPassword(user_id: str, newPassword: str, token:str):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        token_in_db = session.query(TokensForUsers).filter(TokensForUsers.token == token).filter(TokensForUsers.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Error: Token/User does not exist in the database.')
    if not token_in_db:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Token not available in the database.')
    if (token_in_db.expiration_date <= datetime.now()):
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content = 'Error: Token has expired in date: ' + str(token_in_db.expiration_date))
    user.password = (hashlib.sha256(newPassword.encode())).hexdigest()
    session.add(user)
    session.query(TokensForUsers).filter(TokensForUsers.user_id == user_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = (user.username +'\'s password has been correctly changed.'))

@router.patch('/{user_id}/set_sub')
async def setSubscription(user_id: str, sub_level: int):
    if sub_level > 2 or sub_level < 0:
        return JSONResponse(status_code = status.HTTP_406_NOT_ACCEPTABLE, content = 'Sub Level ' + str(sub_level) + ' is not allowed. Sub levels are: 0 (Free), 1 (Standard), 2 (Premium)')
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Error: User does not exist in the database.')
    if not user:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'User not available in the database.')
    user.sub_level = sub_level
    session.add(user)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = (user.username +'\'s Sub Level has been correctly set.'))

@router.patch('/{user_id}/set_location')
async def setLocation(user_id: str, latitude: float, longitude: float):
    if latitude > 90 or latitude < -90:
        return JSONResponse(status_code = status.HTTP_406_NOT_ACCEPTABLE, content = "Latitude " + str(latitude) + " is not a valid latitude. It must be between -90 and 90")
    if longitude > 180 or longitude < -180:
        return JSONResponse(status_code = status.HTTP_406_NOT_ACCEPTABLE, content = "Longitude " + str(longitude) + " is not a valid longitude. It must be between -180 and 180")
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Error: User does not exist in the database.')
    if not user:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'User not available in the database.')
    user.latitude = latitude
    user.longitude = longitude
    session.add(user)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = (user.username +'\'s location has been correctly set.'))