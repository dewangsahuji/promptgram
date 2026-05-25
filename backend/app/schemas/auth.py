from pydantic import BaseModel
from pydantic import EmailStr

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token:str
    token_type:str

class UserLogin(BaseModel):
    email: EmailStr
    password: str