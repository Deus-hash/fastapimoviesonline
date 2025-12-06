from pydantic import BaseModel

class Movietop(BaseModel):
    name: str
    id: int
    cost: int
    director: str

class NewMovie(BaseModel):
    title: str
    director: str
    year: int
    oscar: bool

class User(BaseModel):
    username: str
    password: str
    role: str = "user"
    created_at: str = None

class UserLogin(BaseModel):
    username: str
    password: str

class Session(BaseModel):
    username: str
    created_at: str
    expires_at: str
    last_accessed: str