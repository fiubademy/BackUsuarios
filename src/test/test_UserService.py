import pytest
import asyncio
import json
import sys
import os
import hashlib
from fastapi import status
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "service"))
from calls import ApiCalls
from baseService.DataBase import test_engine, Base
import requests


@pytest.mark.asyncio
async def get_token(user_id):
    return await ApiCalls.getTokenForRecPasswd(user_id = user_id)

@pytest.mark.asyncio
async def run_post():
    return await ApiCalls.createUser(username='Nombre_test_123', email='asdasd@qwe.com', password='123456')

@pytest.mark.asyncio
async def run_post_same_uname():
    return await ApiCalls.createUser(username='Nombre_test_123', email='as@qwe.com', password='123456')

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
    return await ApiCalls.patchUser(user_id = user_id, email=email, username=username)

@pytest.mark.asyncio
async def change_password(user_id, oldPass, newPass):
    return await ApiCalls.changePassword(user_id = user_id, oldPassword=oldPass, newPassword=newPass)

@pytest.mark.asyncio
async def recover_password(email, newPass, token):
    return await ApiCalls.recoverPassword(email = email, newPassword=newPass, token=token)

@pytest.mark.asyncio
async def set_sub(user_id, sub_level):
    return await ApiCalls.setSubscription(user_id = user_id, sub_level = sub_level)

@pytest.mark.asyncio
async def set_location(user_id, latitude, longitude):
    return await ApiCalls.setLocation(user_id = user_id, latitude = latitude, longitude=longitude)

@pytest.mark.asyncio
async def toggleBlock(user_id):
    return await ApiCalls.toggleBlockUser(user_id)

@pytest.mark.asyncio
async def login(email, password):
    return await ApiCalls.loginUser(email=email, password=password)

@pytest.mark.asyncio
async def loginAdmin(email, password):
    return await ApiCalls.loginAdmin(email = email, password = password)

@pytest.mark.asyncio
async def registerAdmin(email, password, username):
    return await ApiCalls.createAdmin(email = email, password = password, username = username)


Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)
ApiCalls.set_engine(test_engine)

def test_post_to_db_correctly():
    user_id = asyncio.run(run_post())['user_id']
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'Nombre_test_123'
    assert user_obtained["email"] == 'asdasd@qwe.com'
    asyncio.run(run_delete(user_id))

def test_post_admin_to_db_correctly():
    user_id = asyncio.run(registerAdmin('admin@admin.com', 'password', 'admin'))['user_id']
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'admin'
    assert user_obtained["email"] == 'admin@admin.com'
    asyncio.run(run_delete(user_id))

def test_post_repeated_email_should_fail():
    user_id = asyncio.run(run_post())["user_id"]
    assert asyncio.run(run_post()).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_post_repeated_username_should_be_ok():
    user_id = asyncio.run(run_post())["user_id"]
    call = asyncio.run(run_post_same_uname())
    user_id_two = call["user_id"]
    assert user_id_two != user_id
    asyncio.run(run_delete(user_id))
    asyncio.run(run_delete(user_id_two))
    
def test_delete_from_db_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained["user_id"] == user_id
    assert user_obtained["username"] == 'Nombre_test_123'
    assert user_obtained["email"] == 'asdasd@qwe.com'
    asyncio.run(run_delete(user_id))
    assert asyncio.run(run_get_by_id(user_id)).status_code == status.HTTP_404_NOT_FOUND

def test_delete_from_db_of_an_unknown_uid_throws_404():
    asyncio.run(run_delete('id_no_existente')).status_code == status.HTTP_404_NOT_FOUND

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

def test_patch_user_db_with_an_incorrect_email():
    user_id = asyncio.run(run_post())["user_id"]
    user_id_two = asyncio.run(run_post_second_user())["user_id"]
    assert asyncio.run(run_patch(user_id, 'asdasd@qweas.com', 'AnUsername')).status_code == status.HTTP_400_BAD_REQUEST
    asyncio.run(run_delete(user_id))
    asyncio.run(run_delete(user_id_two))

def test_patch_with_username_already_used_works():
    user_id = asyncio.run(run_post())["user_id"]
    user_id_two = asyncio.run(run_post_second_user())["user_id"]
    user_dict = asyncio.run(run_patch(user_id, 'testing@testing.net', 'Nombre_Test_1234'))
    assert user_dict['user_id'] == user_id
    assert user_dict['username'] == 'Nombre_Test_1234'
    assert user_dict['email'] == 'testing@testing.net'
    asyncio.run(run_delete(user_id))
    asyncio.run(run_delete(user_id_two))

def test_change_password_correctly():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(change_password(user_id, '123456', '1234567')).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_change_password_with_wrong_old_password_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(change_password(user_id, '1234567', '123456789')).status_code == status.HTTP_400_BAD_REQUEST
    asyncio.run(run_delete(user_id))

def test_recover_password():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    token = asyncio.run(get_token(user_id))
    assert asyncio.run(recover_password('asdasd@qwe.com', '1234567', token)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_recover_password_without_existing_token():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(recover_password('asdasd@qwe.com', '1234567', 'unexistentToken')).status_code == status.HTTP_404_NOT_FOUND
    asyncio.run(run_delete(user_id))

def test_sub_level():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_sub(user_id,1)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_sub_level_less_than_zero_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_sub(user_id,-1)).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_sub_level_more_than_two_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_sub(user_id,3)).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_location():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_location(user_id,-45.33, -75.55)).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_location_latitude_less_than_minus_ninety_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_location(user_id,-90.33, -75.55)).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_location_latitude_greater_than_ninety_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_location(user_id,90.33, -75.55)).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_location_longitude_less_than_minus_hundred_eighty_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_location(user_id,-45.33, -185.55)).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_location_latitude_greater_than_hundred_eighty_fails():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(set_location(user_id,-45.33, 185.55)).status_code == status.HTTP_406_NOT_ACCEPTABLE
    asyncio.run(run_delete(user_id))

def test_block_user():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained['is_blocked'] == 'N'
    assert asyncio.run(toggleBlock(user_id)).status_code == status.HTTP_202_ACCEPTED
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained['is_blocked'] == 'Y'
    asyncio.run(run_delete(user_id))


def test_unblock_user():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained['is_blocked'] == 'N'
    assert asyncio.run(toggleBlock(user_id)).status_code == status.HTTP_202_ACCEPTED
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained['is_blocked'] == 'Y'
    assert asyncio.run(toggleBlock(user_id)).status_code == status.HTTP_202_ACCEPTED
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert user_obtained['is_blocked'] == 'N'
    asyncio.run(run_delete(user_id))

def test_correct_login():
    user_id = asyncio.run(run_post())["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(login(user_obtained['email'], '123456')).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))

def test_login_not_existent_user():
    assert asyncio.run(login('no_email@asd.com', 'noExisto')).status_code == status.HTTP_401_UNAUTHORIZED

def test_login_admin_not_existent_user():
    assert asyncio.run(loginAdmin('no_email@asd.com', 'noExisto')).status_code == status.HTTP_401_UNAUTHORIZED

def test_correct_login_admin():
    user_id = asyncio.run(registerAdmin('admin@admin.com', 'password', 'username'))["user_id"]
    user_obtained = asyncio.run(run_get_by_id(user_id))
    assert asyncio.run(loginAdmin('admin@admin.com', 'password')).status_code == status.HTTP_202_ACCEPTED
    asyncio.run(run_delete(user_id))