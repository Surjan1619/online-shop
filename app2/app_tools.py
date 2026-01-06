from pydantic import BaseModel
from pathlib import Path
import jwt
from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import Depends, Body, HTTPException

import uuid


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"



load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITH")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES"))

class UserPyd(BaseModel):
    username: str
    password: str

class ProductPyd(BaseModel):
    title: str
    price: float
    owner_id: int

"""this function returns result of decoded token if there is
no key and returns user if key is "get_user" """
def token_decode(token,key=None):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = payload.get("sub")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token, no user")
    if key == "get_user":
        return user
    if key is None:
        return payload
    else:
        raise KeyError(f'broken function - "token_decode" ---->{key}')


"func calling example:  create_access_token({'sub': 'user_username'})  "
def create_access_token(data: dict):
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"Something went wrong: {e}")
        raise HTTPException(status_code=401, detail="Invalid data")


def get_file_extention(filename : str):
    return os.path.splitext(filename)[1]

def get_uniq_filename(filename : str):
    ext = get_file_extention(filename)
    return f"{uuid.uuid4()}{ext}"