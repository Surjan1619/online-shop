from sqlalchemy import create_engine, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import sessionmaker, DeclarativeBase,  Session
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional


engine = create_engine('sqlite:///shop_db.db')


from typing import List, Optional
from sqlalchemy import String, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

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



def create_user(userdata: User):

    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.add(userdata)
        session.commit()
        print("User created successfully")
    except Exception as e:
        session.rollback()
        return False
        print(e)
    finally:
        session.close()
        print("Session closed")
    return True

"""
producty uni 
7 pnkt
id
title
priceowner_id
main_url




"""





"""petqa unenanq CRUD API
qayler
1sksnq nranic vor stexcenq avelacnelu API
1.1 skzbic ogtater stexcelu API
1.2 heto apranc stexcelu
1.x amenaverjum zbaxvenq nk-neri het
"""
