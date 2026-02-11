import shutil
from fastapi import FastAPI, UploadFile, Form, Depends, File
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List, Optional
from pathlib import Path
from starlette.responses import FileResponse
from app_tools import (UserPyd,
                       create_access_token,
                       get_uniq_filename,
                       ProductPyd, ImagePyd,
                       token_decode,
                       get_seller_products,
                       compress_image)
from io_db_tools import (User, Product, Image,
                         create_user,
                         check_logining_user,
                         get_product_by_id,
                         get_user,
                         create_product,
                         create_image,
                         get_random_products,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.post("/registrate-user")
async def create_us(user: UserPyd):
    #creating alchmy model of the user
    user = User(username=user.username, password=user.password)
    #adding it int the DB and getting his id
    creating_result = await create_user(user)
    if creating_result:
        print(creating_result)
        token = create_access_token({"sub" : user.id})
    else:
        raise HTTPException(status_code=409, detail="User with this username already exists")
    return {"status": "ok",
            "token": token}


@app.get("/login")
async def login_page():
    return FileResponse(STATIC_DIR / "login_page.html")

@app.post("/login-user")
async def login(user_data: UserPyd):

    #creating alchemy model of the user
    user = User(username=user_data.username, password=user_data.password)
    #checking user in DB and getting ID
    user_id = await check_logining_user(user)
    #checking if BD founed user and returned his ID
    if user_id:
        #creating token with user ID
        token = create_access_token({"sub" : user_id})
        #returning user new token
        print(token)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")


@app.get("/main_page")
async def main_page():
    return FileResponse(STATIC_DIR / "main_page.html")


@app.get("/get-products")
async def get_products_():
    return {"status": "ok",
            "products": await get_random_products()
            }


@app.get("/product-details")
async def product_details_page():
    return FileResponse(STATIC_DIR / "product_details_page.html")


@app.get("/get-product/{product_id}")
async def get_product_id(product_id: int):
    product = await get_product_by_id(product_id)
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
    return {"status": "ok",
            "product": product}


@app.get("/create_product")
async def create_product_page():
    return FileResponse(STATIC_DIR / "create_product_page.html")

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
    content = await main_image.read()
    compressed_image = compress_image(content)
    unic_filename = get_uniq_filename(main_image.filename)
    #creating main image directory
    file_path = os.path.join(MEDIA_FOLDER, unic_filename)
    #creating main image
    with open(file_path, "wb") as buffer:
        buffer.write(compressed_image)

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
    product = await create_product(product)
    if images:
        for image in images:
            content = await image.read()
            compressed_image = compress_image(content)
            # creating uniq filename
            filename = get_uniq_filename(image.filename)
            # changing extantion
            filename = os.path.splitext(filename)[0] + ".webp"
            #creating file path
            file_path = os.path.join(MEDIA_FOLDER, filename)
            #saving file
            with open(file_path, "wb") as buffer:
                buffer.write(compressed_image)

            await create_image(Image(product_id=product, image_url=file_path))
    return {"status": "ok"}


@app.get("/edit-product")
async def redact_product_page():
    return FileResponse(STATIC_DIR / "product_redact_page.html")

@app.post("/redact-product")
async def patch_product(product : ProductPyd, token: str = Depends(oauth2_scheme)):
    user = token_decode(token, key="get_user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user == product.owner_id or await get_user(user) == "Admin":
        if await redact_product(product.id, product.title, product.description, product.price):
            return {"status": "ok", }
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@app.delete("/delete-product/{product_id}")
async def post_delete(product_id : int, token: str = Depends(oauth2_scheme)):
    user = token_decode(token, key="get_user")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if await delete_product(product_id, user):
        return {"status": "ok",}
    else:
        raise HTTPException(status_code=404, detail="Something went wrong")


# petqa html ejum poxvi zaprosy
@app.get("/get-current-user")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    return {"id": token_decode(token)['sub']}


@app.get("/go-to-profile/{id}")
async def go_to_profile_page():
    return FileResponse(STATIC_DIR / "profile_page.html")


@app.get("/profile/{id}")
async def user_profile(id: int, token: str = Depends(oauth2_scheme)):
    role = None
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        user_id = token_decode(token)['sub']
        products = await get_seller_products(id)
        if id == int(user_id) or await get_user(user_id) == "Admin":
            role = "owner"
            print("owner entered")

        return {"status": "ok",
                "username": await get_user(id),
                "products": products,
                "role": role}
