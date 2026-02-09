from fastapi import HTTPException
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession)
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Numeric, func
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, DatabaseError

"""ORM models"""


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    products: Mapped[List["Product"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(1500), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"))

    main_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    owner: Mapped["User"] = relationship(back_populates="products")
    images: Mapped[List["Image"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )

    def __str__(self):
        print(self.id, self.title, self.description, self.price, self.owner_id, [i.image_url for i in self.images])


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )

    image_url: Mapped[str] = mapped_column(String(255), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="images")


"""DB connection and setting"""
DB_URL = "postgresql+asyncpg://shop:1234@localhost/online_shop"
engine = create_async_engine(DB_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session():
    async with SessionLocal() as session:
        yield session


"""CRUD operations"""


async def create_user(userdata: User):
    async with SessionLocal() as session:
        try:
            session.add(userdata)
            await session.commit()
            await session.refresh(userdata)
            return userdata.id
        except IntegrityError:
            await session.rollback()
            return False


async def check_logining_user(userdata: User):
    async with SessionLocal() as session:
        try:
            stmt = select(User).where(User.username == userdata.username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            return user.id
        except DatabaseError:
            raise HTTPException(status_code=500, detail="error while checking user")


# async def get_user_id(username):
#     async with SessionLocal() as session:
#         try:
#             stmt = select(User).where(User.username == username)
#             result = await session.execute(stmt)
#             user = result.scalars().first()
#             if not user:
#                 return None
#             return user.id
#         except DatabaseError:
#             raise HTTPException(status_code=500, detail="error while getting user id")

async def get_product_by_id(product_id: int):
    async with SessionLocal() as session:
        try:
            stmt = select(Product).options(selectinload(Product.images)).where(Product.id == product_id)
            result = await session.execute(stmt)
            product = result.scalars().first()
            if not product:
                raise HTTPException(status_code=404, detail="product not found")
            return product
        except DatabaseError:
            raise HTTPException(status_code=500, detail="error while getting product by id")


async def get_user_all_data(user_id):
    async with SessionLocal() as session:
        try:
            stmt = select(User).options(selectinload(User.products).selectinload(Product.images)).where(
                User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if not user:
                return None
            return user
        except DatabaseError:
            await session.rollback()
            raise HTTPException(status_code=500, detail="error while getting user by id")


async def get_user(data):
    async with SessionLocal() as session:
        try:
            data = int(data)
            stmt = select(User).where(User.id == data)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if not user:
                raise HTTPException(status_code=404, detail="user not found")
            return user.username
        except DatabaseError:
            raise HTTPException(status_code=500, detail="error while getting user")


async def create_product(product: Product):
    async with SessionLocal() as session:
        try:
            session.add(product)
            await session.commit()
            await session.refresh(product)
            print("Product created successfully")
            return product.id
        except DatabaseError:
            await session.rollback()
            raise HTTPException(status_code=500, detail="error while creating product")


async def create_image(imagedata: Image):
    async with SessionLocal() as session:
        try:
            session.add(imagedata)
            await session.commit()
            await session.refresh(imagedata)
            print("Image data created successfully")
            return imagedata.id
        except DatabaseError:
            await session.rollback()
            raise HTTPException(status_code=500, detail="error while creating image")


async def get_random_products():
    async with SessionLocal() as session:
        try:
            stmt = select(Product).options(selectinload(Product.images)).order_by(func.random()).limit(12)
            result = await session.execute(stmt)
            products = result.scalars().all()
            return products
        except DatabaseError:
            raise HTTPException(status_code=500, detail="error while getting products")


async def redact_product(id, title, description, price, ):
    async with SessionLocal() as session:
        try:
            print(type(id), id, 10 * "\n")
            old_product = await session.get(Product, id)
            # readcting all data about product
            old_product.title = title
            old_product.description = description
            old_product.price = price
            await session.commit()
            await session.refresh(old_product)
            print("product is sucessfully updated")
            return True
        except DatabaseError:
            await session.rollback()
            raise HTTPException(status_code=500, detail="error while updating product")


async def delete_product(product_id: int, user_id):
    async with SessionLocal() as session:
        try:
            stmt = select(Product).where(Product.id == product_id)
            result = await session.execute(stmt)
            product = result.scalars().first()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            if product.owner_id != user_id or get_user(user_id) != "Admin":
                raise HTTPException(status_code=403, detail="You are not the owner of this product")
            await session.delete(product)
            await session.commit()
            return True
        except DatabaseError:
            await session.rollback()
            raise HTTPException(status_code=500, detail="error while deleting product")
