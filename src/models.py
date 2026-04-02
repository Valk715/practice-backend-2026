from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    bookings = relationship("Booking", back_populates="owner")
    reviews = relationship("Review", back_populates="author")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    capacity = Column(Integer)
    equipment = Column(String)
    category = Column(String)
    bookings = relationship("Booking", back_populates="resource")
    reviews = relationship("Review", back_populates="resource")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String, default="active")
    owner = relationship("User", back_populates="bookings")
    resource = relationship("Resource", back_populates="bookings")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"))
    rating = Column(Integer)
    comment = Column(String)
    author = relationship("User", back_populates="reviews")
    resource = relationship("Review", back_populates="reviews")