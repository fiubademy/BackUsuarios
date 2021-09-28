from fastapi import FastAPI, status
from typing import List, Optional
from pydantic import EmailStr
from pydantic.main import BaseModel
from starlette.responses import JSONResponse
import uvicorn
import uuid

app = FastAPI()

users = {}

class UserRequest(BaseModel):
    username: str
    userId: str
    email: str

class UserResponse(BaseModel):
    userId: str
    username: str
    email: str

class User:
    def __init__(self, id: str, username: str, email: str, password: str):
        self.userId =  id
        self.username = username
        self.email = email
        self.password = password

@app.get('/users', response_model = List[UserResponse], status_code=status.HTTP_200_OK)
async def getUsers(emailFilter: Optional[str] = None, usernameFilter: Optional[str] = None):
    if len(users) == 0:
        return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content= 'No users found in the database.')
    mensaje = []
    for userId, user in users.items():
        cumpleFiltro = True
        if(usernameFilter is not None and not user.username.startswith(usernameFilter)):
            cumpleFiltro = False
        if(emailFilter is not None and not user.email.startswith(emailFilter) and cumpleFiltro == True):
            cumpleFiltro = False
        if(cumpleFiltro):
            mensaje.append ({'userId':userId, 'username':user.username, 'email':user.email})
    return mensaje

@app.get('/users/{userId}', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def getUser(userId= None):
    if userId is None:
        return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content='Cannot search for null users.')
    if (userId not in users):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + userId + ' not found.')
    return {'username': users[userId].username, 'userId': users[userId].userId, 'email': users[userId].email}

@app.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def createUser(username, email, password):
    userId = str(uuid.uuid4())
    newUser = User(id=userId, username=username, email=email, password=password)
    users[userId] = newUser
    return {'userId':userId, 'username':username, 'email':email}

@app.delete('/users/{userId}', status_code=status.HTTP_202_ACCEPTED)
async def deleteUser(userId):
    if (userId not in users):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + userId + ' not found and will not be deleted.')
    users.pop(userId)
    return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content='User ' + userId + 'was deleted succesfully.')

@app.patch('/users/{userId}')
async def patchUser(userId: str, email: Optional[str] = None, username: Optional[str] = None):
    if(users[userId] == None):
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content='User ' + userId + ' not found and will not be patched.')
    if(email is not None):
        users[userId].email = email
    if(username is not None):
        users[userId].username = username
    return {'userId': userId, 'username':users[userId].username, 'email':users[userId].email}


@app.patch('/users/changePassword/{userId}')
async def changePassword(userId: str, oldPassword: str, newPassword: str):
    if(users[userId] is not None):
        if(oldPassword != users[userId].password):
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content = 'Your old password is not correct.')
        users[userId].password = newPassword
        return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = (users[userId].username +'\'s password has been correctly changed.'))
    return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'User ' + userId + ' was not found in the database')

@app.patch('/users/recoverPassword/{userId}')
async def recoverPassword(userId: str, newPassword: str):
    if(users[userId] is not None):
        users[userId].password = newPassword
        return JSONResponse(status_code = status.HTTP_202_ACCEPTED, content = (users[userId].username +'\'s password has been correctly changed.'))
    return JSONResponse(status_code = status.HTTP_404_NOT_FOUND, content = 'User ' + userId + ' was not found in the database')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
    