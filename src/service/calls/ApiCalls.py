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

@router.get('/{page_num}', status_code=status.HTTP_200_OK)
async def getUsers(page_num: int, emailFilter: Optional[str] = '', usernameFilter: Optional[str] = ''):
    mensaje = []
    try:
        count = session.query(User).filter(User.email.like("%"+emailFilter+"%")).filter(User.username.like("%"+usernameFilter+"%")).count()
        users = session.query(User).filter(User.email.like("%"+emailFilter+"%")).filter(User.username.like("%"+usernameFilter+"%")).limit(PER_PAGE).offset((page_num-1) * PER_PAGE)
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content= 'No users found in page ' + str(page_num) + ' in the database.')
    if (users.count() == 0):
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content= 'No users found in page ' + str(page_num) + ' in the database.')
    for user in users:
        mensaje.append ({'user_id':user.user_id, 
                        'username':user.username, 
                        'email':user.email, 
                        'latitude':user.latitude, 
                        'longitude': user.longitude, 
                        'sub_level': user.sub_level,
                        'is_blocked': user.is_blocked,
                        'user_type': user.user_type})
    return {'num_pages': int(count/PER_PAGE) + 1,'content':mensaje}

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
    return{'user_id':user.user_id, 
            'username':user.username, 
            'email':user.email, 
            'latitude':user.latitude, 
            'longitude': user.longitude, 
            'sub_level': user.sub_level,
            'is_blocked': user.is_blocked,
            'user_type': user.user_type}

@router.post('/get_token', response_model=str, status_code=status.HTTP_200_OK)
async def getTokenForRecPasswd(email:str):

    token = str(uuid.uuid4())
    user = session.query(User).filter(User.email == email).first()
    user_id = user.user_id
    if not user:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'User with email ' + email + ' does not exist in the database')
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
                    sub_level = null(),
                    is_blocked = 'N',
                    user_type = 'USER')
    session.add(newUser)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content='Email ' + email + ' already registered as a user.')
    return {'user_id':newUser.user_id, 
            'username':newUser.username, 
            'email':newUser.email, 
            'latitude':newUser.latitude, 
            'longitude': newUser.longitude, 
            'sub_level': newUser.sub_level,
            'is_blocked': newUser.is_blocked,
            'user_type': newUser.user_type}

@router.post('/createAdmin', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def createAdmin(username: str, email: EmailStr, password: str):
    user_id = str(uuid.uuid4())
    newUser = User(user_id=user_id, 
                    username=username, 
                    email=email, 
                    password=(hashlib.sha256(password.encode())).hexdigest(),
                    latitude = null(),
                    longitude = null(),
                    sub_level = null(),
                    is_blocked = 'N',
                    user_type = 'ADMIN')
    session.add(newUser)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return JSONResponse(status_code=status.HTTP_406_NOT_ACCEPTABLE, content='Email ' + email + ' already registered as a user.')
    return {'user_id':newUser.user_id, 
            'username':newUser.username, 
            'email':newUser.email, 
            'latitude':newUser.latitude, 
            'longitude': newUser.longitude, 
            'sub_level': newUser.sub_level,
            'is_blocked': newUser.is_blocked,
            'user_type': newUser.user_type}

@router.delete('/{user_id}', status_code=status.HTTP_202_ACCEPTED)
async def deleteUser(user_id):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found and will not be deleted.')
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found and will not be deleted.')
    session.query(User).filter(User.user_id == user_id).delete()
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content='User ' + user_id + ' was deleted succesfully.')

@router.patch('/{user_id}')
async def patchUser(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if email != None:
            check_non_repeated = session.query(User).filter(User.email == email).first()
            if check_non_repeated != None:
                return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Email '+ email +' is already in use. User has not been patched.')
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found and will not be patched.')
    if(email is not None):
        user.email = email
    if(username is not None):
        user.username = username
    session.add(user)
    session.commit()
    return {'user_id':user.user_id, 
            'username':user.username, 
            'email':user.email, 
            'latitude':user.latitude, 
            'longitude': user.longitude, 
            'sub_level': user.sub_level,
            'is_blocked': user.is_blocked,
            'user_type': user.user_type}


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
    

@router.patch('/recoverPassword/{token}')
async def recoverPassword(newPassword: str, token:str):
    try:
        tok_user = session.query(TokensForUsers).filter(TokensForUsers.token == token).first()
        if not tok_user:
            return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Error: Token not existent')
        user_id = tok_user.user_id
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Error: User does not exist in the database.')
        token_in_db = session.query(TokensForUsers).filter(TokensForUsers.token == token).filter(TokensForUsers.user_id == user.user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Error: Token/User does not exist in the database.')
    if not token_in_db:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'Token not available in the database.')
    if (token_in_db.expiration_date <= datetime.now()):
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content = 'Error: Token has expired in date: ' + str(token_in_db.expiration_date))
    user.password = (hashlib.sha256(newPassword.encode())).hexdigest()
    session.add(user)
    session.query(TokensForUsers).filter(TokensForUsers.user_id == user.user_id).delete()
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

@router.patch('/{user_id}/toggleBlock')
async def toggleBlockUser(user_id: str):
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
    except NoResultFound as err:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found.')
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + user_id + ' not found.')
    print(user)
    if user.is_blocked == "N":
        user.is_blocked = "Y"
    elif user.is_blocked == "Y":
        user.is_blocked = "N"
    session.add(user)
    session.commit()
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = user.username +"'s block state has been toggled.")

@router.post('/login')
async def loginUser(email:str, password:str):
    try:
        user = session.query(User).filter(User.email == email).filter(User.user_type == 'USER').first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content = "User with that email does not exist in the database.")
    if not user:
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content = "User with that email does not exist in the database.")
    if user.password != hashlib.sha256(password.encode()).hexdigest():
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Wrong password for that user.")
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content = user.user_id)

@router.post('/loginAdmin')
async def loginAdmin(email:str, password:str):
    try:
        user = session.query(User).filter(User.email == email).filter(User.user_type == 'ADMIN').first()
    except NoResultFound as err:
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content = "Admin with that email does not exist in the database.")
    if not user:
        return JSONResponse(status_code = status.HTTP_401_UNAUTHORIZED, content = "Admin with that email does not exist in the database.")
    if user.password != hashlib.sha256(password.encode()).hexdigest():
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Wrong password for that Admin user.")
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content = user.user_id)

