from pydantic import BaseModel


class AuthRequest(BaseModel):
    pin: str


class AuthResponse(BaseModel):
    token: str
