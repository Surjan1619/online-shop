import shutil

from fastapi import FastAPI, UploadFile, Form, Depends, File
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional
import uuid
from pathlib import Path
from starlette.responses import FileResponse

from app_tools import UserPyd, create_access_token, get_uniq_filename, ProductPyd, token_decode
from database_tools import User, Product, Image,  create_user, create_product, create_image, get_random_products
from database_tools import check_logining_user, get_product_by_id

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
MEDIA_FOLDER = "media/images"
os.makedirs(MEDIA_FOLDER, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def join_page():
    return FileResponse(STATIC_DIR / "entering_page.html")

@app.get("/register")
async def register():
    return FileResponse(STATIC_DIR / "registration_page.html")

@app.get("/login")
async def login_page():
    return FileResponse(STATIC_DIR / "login_page.html")

@app.get("/main_page")
async def main_page():
    return FileResponse(STATIC_DIR / "main_page.html")

@app.get("/create_product")
async def create_product_page():
    return FileResponse(STATIC_DIR / "create_product_page.html")

@app.get("/product-details")
async def product_details_page():
    print("here product_details_page")
    return FileResponse(STATIC_DIR / "product_details_page.html")

@app.post("/registrate-user")
async def create_us(user: UserPyd):
    #creating alchmy model of the user
    user = User(username=user.username, password=user.password)
    #adding it int the DB and getting his id
    creating_result = create_user(user)
    if creating_result:
        print(creating_result)
        token = create_access_token({"sub" : user.id})
    else:
        raise HTTPException(status_code=409, detail="User with this username already exists")
    return {"status": "ok",
            "token": token}

@app.post("/login-user")
async def login(user_data: UserPyd):

    #creating alchemy model of the user
    user = User(username=user_data.username, password=user_data.password)
    #checking user in DB and getting ID
    user_id = check_logining_user(user)
    #checking if BD founed user and returned his ID
    if user_id:
        #creating token with user ID
        token = create_access_token({"sub" : user_id})
        #returning user new token
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
@app.post("/create-product")
async def get_product_data(
        title: str = Form(...),
        description: str = Form(...),
        price: float = Form(...),
        main_image: UploadFile = File(...),
        images : Optional[List[UploadFile]] = File(None),
        user = Depends(oauth2_scheme),

):

    user = token_decode(user, key="get_user")

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    os.makedirs(MEDIA_FOLDER, exist_ok=True)
    #gitting unique filename
    unic_filename = get_uniq_filename(main_image.filename)
    #creating main image directory
    file_path = os.path.join(MEDIA_FOLDER, unic_filename)
    #creating main image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(main_image.file, buffer)
    #getting user id and creating SQL alchemy model of the product to add itinto database
    user_id = user


    product = Product(
        title=title,
        description=description,
        price=price,
        owner_id=user_id,
    )
    # adding prodict into DB and getting his ID
    product = create_product(product)

    if images:
        for image in images:
            filename = get_uniq_filename(image.filename)
            file_path = os.path.join(MEDIA_FOLDER, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)



            create_image(Image(product_id=product, image_url=file_path))

    return {"status": "ok"}


"""function get_random_products is returning random 10products
in list """
@app.get("/get-products")
async def get_products_():
    return {"status": "ok",
        "products" : get_random_products()
}

@app.get("/get-product/{product_id}")
async def get_product_id(product_id: int):
    product = get_product_by_id(product_id)
    print(product.title)
    if not product:
        raise HTTPException(status_code=404, detail="Product noooot found")
    return  {"product" : product}


