import queue
import threading
import asyncio
from PIL import Image as Img
from io import BytesIO
from fastapi.exceptions import HTTPException
from fastapi import UploadFile, Form, Depends, File
from app_tools import get_uniq_filename
from typing import List, Optional
from time import sleep
import os
from io_db_tools import Product, Image, ProductCategory, create_image, create_product, get_ctg_by_id

MEDIA_FOLDER = "media/images"
product_queue = asyncio.Queue()


def compress_image(file_bytes):
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too big")
    else:
        img = Img.open(BytesIO(file_bytes))
        img = img.convert("RGB")
        img.thumbnail((1024, 1024))
        out = BytesIO()
        img.save(out, "WEBP", quality=60)
        return out.getvalue()


async def product_worker():
    while True:
        data = await product_queue.get()

        title = data["title"]
        description = data["description"]
        categories = data["category"]  # list(id)
        price = data["price"]
        main_image = data["main_image"]
        images = data["images"]
        user = data["user"]

        compressed_image = compress_image(main_image["file"])
        unic_filename = get_uniq_filename(main_image["filename"])
        # creating main image directory
        file_path = os.path.join(MEDIA_FOLDER, unic_filename)
        # creating main image
        with open(file_path, "wb") as buffer:
            buffer.write(compressed_image)
        # getting user id and creating SQL alchemy model of the product to add itinto database
        user_id = user
        # ctgies = []
        # for catg in categories:
        #     ctgies.append(await get_ctg_by_id(catg))

        product = Product(
            title=title,
            description=description,
            price=price,
            owner_id=user_id,
            main_url=file_path
        )
        # adding prodict into DB and getting his ID
        product = await create_product(product, categories)
        if images:
            for image in images:
                compressed_image = compress_image(image["file"])
                # creating uniq filename
                filename = get_uniq_filename(image["filename"])
                # changing extantion
                filename = os.path.splitext(filename)[0] + ".webp"
                # creating file path
                file_path = os.path.join(MEDIA_FOLDER, filename)
                # saving file
                with open(file_path, "wb") as buffer:
                    buffer.write(compressed_image)
                await create_image(Image(product_id=product, image_url=file_path))
        product_queue.task_done()
