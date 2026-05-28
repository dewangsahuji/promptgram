from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Returned by /auth/login (access_token JWT) and /auth/api-token (api_token)."""
    access_token: str
    token_type: str = "bearer"


class ApiTokenResponse(BaseModel):
    """Returned by /auth/authorize — the long-lived API token."""
    api_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str

    model_config = {"from_attributes": True}
