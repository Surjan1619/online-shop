from pydantic import BaseModel
from pathlib import Path
import jwt
from jose import jwt
from datetime import datetime, timedelta
import os
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"



class UserPyd(BaseModel):
    username: str
    password: str

