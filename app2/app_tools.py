from inspect import Traceback
from traceback import TracebackException

from pydantic import BaseModel, Field
from pathlib import Path
import jwt
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi import Depends, Body, HTTPException
from typing import List, Optional
import uuid
from database_tools import get_user_all_data, get_user



BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES"))


class UserPyd(BaseModel):
    username: str
    password: str


class ImagePyd(BaseModel):
    product_id : int
    image_url : str


class ProductPyd(BaseModel):
    id : Optional[int] = None
    title: str
    description: str
    price: float
    owner_id: int
    main_url: Optional[str] = None
    images: List[ImagePyd] = Field(default_factory=list)


"""this function returns result of decoded token if there is
no key and returns user if key is "get_user" """
def token_decode(token,key=None):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = int(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token,no user")
    if key == "get_user":
        return user
    if key is None:
        return payload
    else:
        raise KeyError(f'broken function - "token_decode" ---->{key}')


"func calling example:  create_access_token({'sub': 'user_username'})  "
def create_access_token(data: dict):
    try:
        data["sub"] = str(data["sub"])
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


#this function reutns all products of the user by username
def get_seller_products(user_id):
    user = get_user_all_data(user_id)
    products = []
    try:
        if user.products:
            products = [ProductPyd(
                id=product.id,
                title=product.title,
                description=product.description,
                price=product.price,
                owner_id=user_id,
                main_url=product.main_url,
                images=[ImagePyd(product_id=product.id, image_url=img.image_url) for img in product.images if product.images])
                for product in user.products]
    except Exception as e:
            return []
    return products