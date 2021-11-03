import pytest
import asyncio
import json
from fastapi import status
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound

from src.service.calls import ApiCalls
from src.service.DataBase import test_engine, Base
import hashlib

@pytest.mark.asyncio
async def get_token(user_id):
    return await ApiCalls.getTokenForRecPasswd(user_id = user_id)

@pytest.mark.asyncio
async def run_post():
    return await ApiCalls.createUser(username='Nombre_test_123', email='asdasd@qwe.com', password='123456')

@pytest.mark.asyncio
async def run_delete(user_id):
    return await ApiCalls.deleteUser(user_id)

@pytest.mark.asyncio
async def run_get_by_id(user_id):
    return await ApiCalls.getUser(user_id)

@pytest.mark.asyncio
async def run_get_all():
    return await ApiCalls.getAllUsers()

@pytest.mark.asyncio
async def run_post_second_user():
    return await ApiCalls.createUser(username='Nombre_test_1234', email='asdasd@qweas.com', password='123456789')

@pytest.mark.asyncio
async def run_patch(user_id, email=None, username=None):
    return await ApiCalls.patchUser(user_id = user_id, email=email, username=username).json()

@pytest.mark.asyncio
async def change_password(user_id, oldPass, newPass):
    return await ApiCalls.changePassword(user_id = user_id, oldPassword=oldPass, newPassword=newPass)

@pytest.mark.asyncio
async def recover_password(user_id, newPass, token):
    return await ApiCalls.recoverPassword(user_id = user_id, newPassword=newPass, token=token)

@pytest.mark.asyncio
async def set_sub(user_id, sub_level):
    return await ApiCalls.setSubscription(user_id = user_id, sub_level = sub_level)

@pytest.mark.asyncio
async def set_location(user_id, latitude, longitude):
    return await ApiCalls.setLocation(user_id = user_id, latitude = latitude, longitude=longitude)


Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)
ApiCalls.set_engine(test_engine)

def test_post_to_db_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'Nombre_test_123'
    assert user_obtained["email"] == 'asdasd@qwe.com'
    asyncio.run(run_delete(user_id))
    
def test_delete_from_db_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'Nombre_test_123'
    assert user_obtained["email"] == 'asdasd@qwe.com'
    asyncio.run(run_delete(user_id))
    assert asyncio.run(run_get_by_id(user_id)).status_code == status.HTTP_404_NOT_FOUND

def test_patch_user_db_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'Nombre_test_123'
    assert user_obtained["email"] == 'asdasd@qwe.com'
    asyncio.run(run_patch(user_id, 'email_test@test.com', 'Nombre_De_Usuario_Mod_Test'))
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'Nombre_De_Usuario_Mod_Test'
    assert user_obtained["email"] == 'email_test@test.com'
    asyncio.run(run_delete(user_id))

def test_change_password_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(change_password(user_id, '123456', '1234567')).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_recover_password():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    token = asyncio.run(get_token(user_id))
    assert asyncio.run(recover_password(user_id, '1234567', token)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_change_password_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(change_password(user_id, '123456', '1234567')).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_recover_password():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    token = asyncio.run(get_token(user_id))
    assert asyncio.run(recover_password(user_id, '1234567', token)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_sub_level():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_sub(user_id,1)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_location():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_sub(user_id,-45.33, -75.55)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))




