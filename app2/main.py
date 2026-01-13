import shutil
from itertools import product

from fastapi import FastAPI, UploadFile, Form, Depends, File, Body
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional
import uuid
from pathlib import Path
from starlette.responses import FileResponse

from app_tools import (UserPyd,
                       create_access_token,
                       get_uniq_filename,
                       ProductPyd, ImagePyd,
                       token_decode,
                       get_seller_products)

from database_tools import (User,
                            Product,
                            Image,
                            create_user,
                            create_product,
                            create_image,
                            get_random_products)

from database_tools import (check_logining_user,
                            get_product_by_id,
                            get_user_all_data,
                            get_user,
                            redact_product,
                            delete_product)

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/media", StaticFiles(directory="media"), name="media")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
MEDIA_FOLDER = "media/images"
os.makedirs(MEDIA_FOLDER, exist_ok=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)



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
    return FileResponse(STATIC_DIR / "product_details_page.html")

@app.get("/edit-product")
async def redact_product_page():
    return FileResponse(STATIC_DIR / "product_redact_page.html")
@app.get("/go-to-profile")
async def go_to_profile_page():
    return FileResponse(STATIC_DIR / "profile_page.html")

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
        main_url=file_path
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
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = ProductPyd(
        id=product.id,
        title=product.title,
        description=product.description,
        price=product.price,
        owner_id=product.owner_id,
        main_url=product.main_url,
        images=[ImagePyd(product_id=product.id, image_url=img.image_url) for img in product.images if product.images])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return  {"status": "ok",
        "product" : product}

@app.get("/profile/{seller_id}")
async def seller_profile(seller_id : int, token: str = Depends(oauth2_scheme)):
    role = "user"
    products = get_seller_products(seller_id)
    return {"status" : "ok",
            "username" : get_user(seller_id, key="by_id"),
            "products" : products,
            "role": role}

@app.get("/profile")
async def user_profile(token: str = Depends(oauth2_scheme)):
    role = None
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        user_id = token_decode(token, key="get_user")
        products = get_seller_products(user_id)
        if not products:
            raise HTTPException(status_code=404, detail="Product not found")
        if products[0].owner_id == user_id:
            role = "owner"
        return {"status": "ok",
                "username": get_user(user_id, key="by_id"),
                "products": products,
                "role" : role}


@app.post("/redact-product")
async def patch_product(product : ProductPyd, token: str = Depends(oauth2_scheme)):
    user = token_decode(token, key="get_user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user != product.owner_id:
        raise HTTPException(status_code=403, detail="You are not the owner of this product")
    product = Product(
        id=product.id,
        title=product.title,
        description=product.description,
        price=product.price,
        owner_id=product.owner_id,
        main_url=product.main_url,
    )
    if redact_product(product):
        return {"status": "ok",}
    else:
        raise HTTPException(status_code=404, detail="Product not found")



@app.delete("/delete-product/{product_id}")
async def post_delete(product_id : int, token: str = Depends(oauth2_scheme)):
    user = token_decode(token, key="get_user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if delete_product(product_id, user):
        return {"status": "ok",}
    else:
        raise HTTPException(status_code=404, detail="Something went wrong")

    # title: str
    # description: str
    # price: float
    # owner_id: int
    # main_url: str
