import pytest
import asyncio
import json
import sys
import os
import hashlib
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from sqlalchemy.orm.exc import NoResultFound
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "service"))
from calls import ApiCalls
from baseService.DataBase import test_engine, Base
from baseService.UserService import app
import requests

client= TestClient(app)
Base.metadata.drop_all(test_engine)
Base.metadata.create_all(test_engine)
ApiCalls.set_engine(test_engine)


def test_post_to_db_correctly():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    client.delete('/users/'+user_created.json()['user_id'])


def test_get_by_id_correctly():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    get = client.get('/users/ID/' + user_created.json()['user_id'])
    assert get.status_code == status.HTTP_200_OK
    assert get.json()["username"] == user_created.json()["username"]
    assert get.json()["user_id"] == user_created.json()["user_id"]
    assert get.json()["email"] == user_created.json()["email"]
    assert get.json()["sub_level"] == 0
    assert get.json()["user_type"] == "USER"
    client.delete('/users/'+user_created.json()['user_id'])


def test_get__correctly():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    get = client.get('/users/1')
    assert get.status_code == status.HTTP_200_OK
    assert get.json()['num_pages'] == 1
    assert get.json()["content"][0]["username"] == user_created.json()["username"]
    assert get.json()["content"][0]["user_id"] == user_created.json()["user_id"]
    assert get.json()["content"][0]["email"] == user_created.json()["email"]
    assert get.json()["content"][0]["sub_level"] == 0
    assert get.json()["content"][0]["user_type"] == "USER"
    client.delete('/users/'+user_created.json()['user_id'])


def test_post_admin_to_db_correctly():
    create_admin = client.post('/users/createAdmin?email=admin@admin.com&password=password&username=admin')
    assert create_admin.status_code == status.HTTP_201_CREATED
    assert create_admin.json()["email"] == "admin@admin.com"
    assert create_admin.json()["username"] == "admin"
    client.delete('/users/'+create_admin.json()['user_id'])


def test_post_repeated_email_should_fail():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    user_created_two = client.post("/users/?username=USUARIO&email=mail@mail.com&password=123456789")
    assert user_created_two.status_code == status.HTTP_406_NOT_ACCEPTABLE
    client.delete('/users/'+user_created.json()['user_id'])


def test_post_repeated_username_should_be_ok():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    user_created_two = client.post("/users/?username=USUARIO&email=email@mail.com&password=123456789")
    assert user_created_two.status_code == status.HTTP_201_CREATED
    client.delete('/users/'+user_created.json()['user_id'])
    client.delete('/users/'+user_created_two.json()['user_id'])


def test_delete_from_db_correctly():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    delete_status = client.delete('/users/'+user_created.json()['user_id'])
    assert delete_status.status_code == status.HTTP_202_ACCEPTED



def test_delete_from_db_of_an_unknown_uid_throws_404():
    delete_status = client.delete('/users/id_no_existe')
    assert delete_status.status_code == status.HTTP_404_NOT_FOUND


def test_patch_user_db_correctly():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    user_patched = client.patch('/users/'+user_created.json()['user_id']+'?username=USUARIO_EDIT&email=emailedit@mail.com')
    assert user_patched.status_code == status.HTTP_200_OK
    assert user_patched.json()["username"] == "USUARIO_EDIT"
    assert user_patched.json()["user_id"] == user_created.json()["user_id"]
    assert user_patched.json()["email"] == "emailedit@mail.com"
    client.delete('/users/'+user_created.json()['user_id'])


def test_patch_user_db_with_an_incorrect_email():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    user_created_two = client.post('/users/?username=USUARIO&email=email@mail.com&password=123456789')
    assert user_created_two.status_code == status.HTTP_201_CREATED
    assert user_created_two.json()["username"] == "USUARIO"
    assert user_created_two.json()["email"] == "email@mail.com"
    user_patched = client.patch('/users/'+user_created.json()['user_id']+'?username=USUARIO_EDIT&email=email@mail.com')
    assert user_patched.status_code == status.HTTP_400_BAD_REQUEST
    client.delete('/users/'+user_created.json()['user_id'])
    client.delete('/users/'+user_created_two.json()['user_id'])


def test_patch_with_username_already_used_works():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    user_created_two = client.post('/users/?username=USUARIO 2&email=email@mail.com&password=123456789')
    assert user_created_two.status_code == status.HTTP_201_CREATED
    assert user_created_two.json()["username"] == "USUARIO 2"
    assert user_created_two.json()["email"] == "email@mail.com"
    user_patched = client.patch('/users/'+user_created.json()['user_id']+'?username=USUARIO 2')
    assert user_patched.status_code == status.HTTP_200_OK
    assert user_patched.json()["username"] == user_created_two.json()["username"]
    client.delete('/users/'+user_created.json()['user_id'])
    client.delete('/users/'+user_created_two.json()['user_id'])


def test_change_password_correctly():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    mod_password = client.patch('/users/changePassword/'+user_created.json()["user_id"]+'?oldPassword=123456789&newPassword=12345678')
    assert mod_password.status_code == status.HTTP_202_ACCEPTED
    client.delete('/users/'+user_created.json()["user_id"])


def test_change_password_with_wrong_old_password_fails():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    mod_password = client.patch('/users/changePassword/'+user_created.json()["user_id"]+'?oldPassword=1234567890&newPassword=12345678')
    assert mod_password.status_code == status.HTTP_400_BAD_REQUEST
    client.delete('/users/'+user_created.json()["user_id"])


def test_recover_password():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    token = client.post("/users/get_token?email=mail@mail.com")
    assert token.status_code == status.HTTP_200_OK
    mod_password = client.patch('/users/recoverPassword/'+token.json()+'?newPassword=12345678')
    assert mod_password.status_code == status.HTTP_202_ACCEPTED
    client.delete('/users/'+user_created.json()["user_id"])


def test_recover_password_without_existing_token():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    mod_password = client.patch('/users/recoverPassword/TOKEN_UNEXISTENT?newPassword=12345678')
    assert mod_password.status_code == status.HTTP_404_NOT_FOUND
    client.delete('/users/'+user_created.json()["user_id"])


def test_recover_password_invalid_password():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    token = client.post("/users/get_token?email=mail@mail.com")
    assert token.status_code == status.HTTP_200_OK
    mod_password = client.patch('/users/recoverPassword/'+token.json()+'?newPassword=1234567')
    assert mod_password.status_code == status.HTTP_406_NOT_ACCEPTABLE
    client.delete('/users/'+user_created.json()["user_id"])


def test_location():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    location = client.patch('/users/'+user_created.json()['user_id']+'/set_location?latitude=-45.33&longitude=-75.55')
    assert location.status_code == status.HTTP_202_ACCEPTED
    client.delete('/users/'+user_created.json()['user_id'])


def test_location_latitude_less_than_minus_ninety_fails():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    location = client.patch('/users/'+user_created.json()['user_id']+'/set_location?latitude=-95.33&longitude=-75.55')
    assert location.status_code == status.HTTP_406_NOT_ACCEPTABLE
    client.delete('/users/'+user_created.json()['user_id'])


def test_location_latitude_greater_than_ninety_fails():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    location = client.patch('/users/'+user_created.json()['user_id']+'/set_location?latitude=90.33&longitude=-75.55')
    assert location.status_code == status.HTTP_406_NOT_ACCEPTABLE
    client.delete('/users/'+user_created.json()['user_id'])


def test_location_longitude_less_than_minus_hundred_eighty_fails():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    location = client.patch('/users/'+user_created.json()['user_id']+'/set_location?latitude=-95.33&longitude=-185.55')
    assert location.status_code == status.HTTP_406_NOT_ACCEPTABLE
    client.delete('/users/'+user_created.json()['user_id'])


def test_location_latitude_greater_than_hundred_eighty_fails():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    location = client.patch('/users/'+user_created.json()['user_id']+'/set_location?latitude=-95.33&longitude=185.55')
    assert location.status_code == status.HTTP_406_NOT_ACCEPTABLE
    client.delete('/users/'+user_created.json()['user_id'])


def test_block_user():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    block = client.patch('/users/'+user_created.json()['user_id']+'/toggleBlock')
    assert block.status_code == status.HTTP_202_ACCEPTED
    user_get = client.get('/users/ID/'+user_created.json()['user_id'])
    assert user_get.status_code == status.HTTP_200_OK
    assert user_get.json()['is_blocked'] == 'Y'
    client.delete('/users/'+user_get.json()['user_id'])


def test_unblock_user():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    block = client.patch('/users/'+user_created.json()['user_id']+'/toggleBlock')
    assert block.status_code == status.HTTP_202_ACCEPTED
    user_get = client.get('/users/ID/'+user_created.json()['user_id'])
    assert user_get.status_code == status.HTTP_200_OK
    assert user_get.json()['is_blocked'] == 'Y'
    block = client.patch('/users/'+user_created.json()['user_id']+'/toggleBlock')
    assert block.status_code == status.HTTP_202_ACCEPTED
    user_get = client.get('/users/ID/'+user_created.json()['user_id'])
    assert user_get.status_code == status.HTTP_200_OK
    assert user_get.json()['is_blocked'] == 'N'
    client.delete('/users/'+user_get.json()['user_id'])


def test_correct_login():
    user_created = client.post('/users/?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    login = client.post('/users/login?email=mail@mail.com&password=123456789')
    assert login.status_code == status.HTTP_202_ACCEPTED
    client.delete('/users/'+user_created.json()['user_id'])


def test_login_not_existent_user():
    login = client.post('/users/login?email=mail@mail.com&password=123456789')
    assert login.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_admin_not_existent_user():
    login = client.post('/users/loginAdmin?email=mail@mail.com&password=123456789')
    assert login.status_code == status.HTTP_401_UNAUTHORIZED


def test_correct_login_admin():
    user_created = client.post('/users/createAdmin?username=USUARIO&email=mail@mail.com&password=123456789')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()["username"] == "USUARIO"
    assert user_created.json()["email"] == "mail@mail.com"
    login = client.post('/users/loginAdmin?email=mail@mail.com&password=123456789')
    assert login.status_code == status.HTTP_202_ACCEPTED
    client.delete('/users/'+user_created.json()['user_id'])


def test_google_signup_in_login():
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=Usuario Google')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()['is_federated'] == 'Y'
    assert user_created.json()['username'] == 'Usuario Google'
    assert user_created.json()['email'] == 'mail@gmail.com'
    client.delete('/users/deleteGoogle/idgoo')


def test_google_login_correctly():
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=Usuario Google')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()['is_federated'] == 'Y'
    assert user_created.json()['username'] == 'Usuario Google'
    assert user_created.json()['email'] == 'mail@gmail.com'
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=Usuario Google')
    assert user_created.status_code == status.HTTP_202_ACCEPTED
    assert user_created.json()['is_federated'] == 'Y'
    assert user_created.json()['username'] == 'Usuario Google'
    assert user_created.json()['email'] == 'mail@gmail.com'
    client.delete('/users/deleteGoogle/idgoo')

def test_google_login_wrong_username():
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=Usuario Google')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()['is_federated'] == 'Y'
    assert user_created.json()['username'] == 'Usuario Google'
    assert user_created.json()['email'] == 'mail@gmail.com'
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=UsuarioGoogle')
    assert user_created.status_code == status.HTTP_401_UNAUTHORIZED
    client.delete('/users/deleteGoogle/idgoo')


def test_google_login_wrong_email():
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=Usuario Google')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()['is_federated'] == 'Y'
    assert user_created.json()['username'] == 'Usuario Google'
    assert user_created.json()['email'] == 'mail@gmail.com'
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=email@gmail.com&username=UsuarioGoogle')
    assert user_created.status_code == status.HTTP_401_UNAUTHORIZED
    client.delete('/users/deleteGoogle/idgoo')


def test_set_avatar_user_not_existent():
    avatar_change = client.patch('/users/NO_EXISTENTE/set_avatar/2')
    assert avatar_change.status_code == status.HTTP_404_NOT_FOUND


def test_set_avatar_ok():
    user_created = client.post('/users/loginGoogle?idGoogle=idgoo&email=mail@gmail.com&username=Usuario Google')
    assert user_created.status_code == status.HTTP_201_CREATED
    assert user_created.json()['is_federated'] == 'Y'
    assert user_created.json()['username'] == 'Usuario Google'
    assert user_created.json()['email'] == 'mail@gmail.com'
    avatar_change = client.patch('/users/' + user_created.json()['user_id'] + '/set_avatar/2')
    assert avatar_change.status_code == status.HTTP_200_OK
    get_user = client.get('/users/ID/'+user_created.json()['user_id'])
    assert get_user.status_code == status.HTTP_200_OK
    assert get_user.json()['avatar'] == 2
    client.delete('/users/'+user_created.json()['user_id'])


def test_sub_premium():
    create_user = client.post('/users/?username=USUARIO&email=usuario@mail.com&password=123456789')
    assert create_user.status_code == status.HTTP_201_CREATED
    user_id = create_user.json()['user_id']
    request = client.post('/users/' + user_id + '/pay_sub', data='{"type_of_sub":2}')
    assert request.status_code == status.HTTP_200_OK
    get_user = client.get('/users/ID/'+user_id)
    assert get_user.status_code == status.HTTP_200_OK
    assert get_user.json()['sub_level'] == 2
    client.delete('/users/'+user_id)

def test_sub_standard():
    create_user = client.post('/users/?username=USUARIO&email=usuario@mail.com&password=123456789')
    assert create_user.status_code == status.HTTP_201_CREATED
    user_id = create_user.json()['user_id']
    request = client.post('/users/' + user_id + '/pay_sub', data='{"type_of_sub":1}')
    assert request.status_code == status.HTTP_200_OK
    get_user = client.get('/users/ID/'+user_id)
    assert get_user.status_code == status.HTTP_200_OK
    assert get_user.json()['sub_level'] == 1
    client.delete('/users/'+user_id)


def test_sub_premium_overwrites_standard():
    create_user = client.post('/users/?username=USUARIO&email=usuario@mail.com&password=123456789')
    assert create_user.status_code == status.HTTP_201_CREATED
    user_id = create_user.json()['user_id']
    request = client.post('/users/' + user_id + '/pay_sub', data='{"type_of_sub":1}')
    get_user = client.get('/users/ID/'+user_id)
    assert get_user.status_code == status.HTTP_200_OK
    assert get_user.json()['sub_level'] == 1
    request = client.post('/users/' + user_id + '/pay_sub', data='{"type_of_sub":2}')
    assert request.status_code == status.HTTP_200_OK
    get_user = client.get('/users/ID/'+user_id)
    assert get_user.status_code == status.HTTP_200_OK
    assert get_user.json()['sub_level'] == 2
    client.delete('/users/'+user_id)


def test_without_payments_sub_is_free():
    create_user = client.post('/users/?username=USUARIO&email=usuario@mail.com&password=123456789')
    assert create_user.status_code == status.HTTP_201_CREATED
    user_id = create_user.json()['user_id']
    get_user = client.get('/users/ID/'+user_id)
    assert get_user.status_code == status.HTTP_200_OK
    assert get_user.json()['sub_level'] == 0
    client.delete('/users/'+user_id)


def test_pay_invalid_sub():
    create_user = client.post('/users/?username=USUARIO&email=usuario@mail.com&password=123456789')
    assert create_user.status_code == status.HTTP_201_CREATED
    user_id = create_user.json()['user_id']
    request = client.post('/users/' + user_id + '/pay_sub', data='{"type_of_sub":3}')
    assert request.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    request = client.post('/users/' + user_id + '/pay_sub', data='{"type_of_sub":-1}')
    assert request.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
