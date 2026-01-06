import shutil

from fastapi import FastAPI, UploadFile, Form, Depends, File
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
import os
from typing import List
import uuid
from pathlib import Path
from starlette.responses import FileResponse

from app_tools import UserPyd, create_access_token, get_uniq_filename, ProductPyd, token_decode
from database_tools import User, Product, Image,  create_user, create_product, create_image, get_random_products


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
MEDIA_FOLDER = "media/images"
os.makedirs(MEDIA_FOLDER, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def join_page():
    return FileResponse(STATIC_DIR / "testovi.html")

@app.get("/register")
async def register():
    return FileResponse(STATIC_DIR / "registration_page.html")

@app.post("/registrate-user")
async def create_us(user: UserPyd):
    #creating alchmy model of the user
    user = User(username=user.username, password=user.password)
    #adding it int the DB and getting his id
    creating_result = create_user(user)
    if creating_result:
        token = create_access_token({"sub" : user.id})
    else:
        return
    return {"status": "ok",
            "token": token}


@app.post("/create-product")
async def get_product_data(
        title: str = Form(...),
        price: float = Form(...),
        image : UploadFile = File(...),
        user = Depends(oauth2_scheme),
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    os.makedirs(MEDIA_FOLDER, exist_ok=True)
    #gitting unique filename
    unic_filename = get_uniq_filename(image.filename)
    #creating file directory
    file_path = os.path.join(MEDIA_FOLDER, unic_filename)
    #creating file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    #getting user id and creating SQL alchemy model of the product to add itinto database
    user_id = user

    product = Product(
        title=title,
        price=price,
        owner_id=user_id,
    )
    #adding prodict into DB and getting his ID
    product = create_product(product)
    image = Image(product, file_path)
    create_image(image)
    return {"status": "ok"}


"""function get_random_products is returning random 10products
in list """
@app.get("/get-products")
async def get_products_():
    return {"status": "ok",
        "products" : get_random_products()
}

