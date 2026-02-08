from fastapi import HTTPException
from sqlalchemy import create_engine, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy import ForeignKey, Numeric, func
from sqlalchemy.orm import sessionmaker, DeclarativeBase,  Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, Mapped, mapped_column, selectinload
from typing import List, Optional
import os



engine = create_engine('sqlite:///shop_db.db')
MEDIA_FOLDER = "media/images"
os.makedirs(MEDIA_FOLDER, exist_ok=True)


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
class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )

    image_url: Mapped[str] = mapped_column(String(255), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="images")


Base.metadata.create_all(bind=engine)

def create_user(userdata: User):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(userdata)
        session.commit()
        session.refresh(userdata)
        print("User created successfully")
        return userdata.id
    except IntegrityError as e:
        session.rollback()
        print(f"User already exists info >>>{e}")
        return False
    finally:
        session.close()
        print("Session closed")


# created async version  ^^^


def check_logining_user(userdata: User):
    try:

        Session = sessionmaker(bind=engine)
        session = Session()
        user = session.query(User).filter(User.username == userdata.username, User.password == userdata.password).first()

        if user:
            return user.id
        else:
            return False

    finally:
        session.close()


# created async version  ^^^


def get_user_id(username):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        user = session.query.filter(User.username == username).first()
        if not user:
            return None
        return user.id
    finally:
        session.close()


# created async version  ^^^

def get_product_by_id(product_id: int):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        return (session.query(Product).options(selectinload(Product.images)).filter(Product.id == product_id).first())
    finally:
        session.close()


# created async version  ^^^
def get_user(data, key=None):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        if key == "by_id":
            user =  session.query(User).filter(User.id == data).first()
            return user.username
        if key == "by_username":
            user = session.query(User).filter(User.username == data).first()
            return  user.id
        if not key or not data:
            print("incorrect function using\n " * 10)
    finally:
        session.close()


# created async version  ^^^
def create_product(product : Product):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(product)
        session.commit()
        session.refresh(product)
        print("Product created successfully")
        return product.id
    finally:
        session.close()


# created async version  ^^^
def create_image(imagedata: Image):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(imagedata)
        session.commit()
        session.refresh(imagedata)
        print("Image data created successfully")
        return imagedata.id
    finally:
        session.close()


# created async version  ^^^
def get_random_products():
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        products = (session.query(Product).options(selectinload(Product.images)).order_by(func.random()).limit(12).all())
        return products
    finally:
        session.close()


# created async version  ^^^

# out of usage vvv
def get_user_all_data(user_id):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        user = (session.query(User).options(
            selectinload(User.products)
            .selectinload(Product.images))
                .filter(User.id == user_id).first())
        if not user:
            return None
        return user
    except Exception as e:
        print(e)
        session.rollback()
    finally:
        session.close()
"""this function is redacting everyting about product without images """
def redact_product(new_product: Product, ):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        old_product = session.get(Product, new_product.id)
        #readcting all data about product
        old_product.title = new_product.title
        old_product.description = new_product.description
        old_product.price = new_product.price
        old_product.main_url = new_product.main_url
        session.commit()
        session.refresh(old_product)
        print("product is sucessfully updated")
        return True
    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()


# created async version  ^^^

def delete_product(product_id: int, user_id):
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.owner_id != user_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this product")
        session.delete(product)
        session.commit()
        return True
    except Exception as e:
        print("Someting went wrong while deleting product", e)
        session.rollback()
    finally:
        session.close()