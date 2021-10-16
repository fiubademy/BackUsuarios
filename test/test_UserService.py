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

from service import UserService
import hashlib

@pytest.mark.asyncio
async def get_token(user_id):
    return await UserService.getTokenForRecPasswd(user_id = user_id)

@pytest.mark.asyncio
async def run_post():
    return await UserService.createUser(username='Nombre_test_123', email='asdasd@qwe.com', password='123456')

@pytest.mark.asyncio
async def run_delete(user_id):
    return await UserService.deleteUser(user_id)

@pytest.mark.asyncio
async def run_get_by_id(user_id):
    return await UserService.getUser(user_id)

@pytest.mark.asyncio
async def run_get_all():
    return await UserService.getAllUsers()

@pytest.mark.asyncio
async def run_post_second_user():
    return await UserService.createUser(username='Nombre_test_1234', email='asdasd@qweas.com', password='123456789')

@pytest.mark.asyncio
async def run_patch(user_id, email=None, username=None):
    return await UserService.patchUser(user_id = user_id, email=email, username=username)

@pytest.mark.asyncio
async def change_password(user_id, oldPass, newPass):
    return await UserService.changePassword(user_id = user_id, oldPassword=oldPass, newPassword=newPass)

@pytest.mark.asyncio
async def recover_password(user_id, newPass, token):
    return await UserService.recoverPassword(user_id = user_id, newPassword=newPass, token=token)

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


