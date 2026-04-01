from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager
from . import models, schemas, auth, database


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    if db.query(models.Resource).count() == 0:
        db.add_all([
            models.Resource(name="Cyber Loft", description="Gaming zone", capacity=10, equipment="PC, PS5"),
            models.Resource(name="Meeting Room", description="Business zone", capacity=5, equipment="Projector")
        ])
        db.commit()
    db.close()
    yield


app = FastAPI(title="Booking API", lifespan=lifespan)


@app.post("/register", response_model=schemas.UserOut, tags=["Auth"])
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email registered")
    new_user = models.User(email=user.email, hashed_password=auth.get_password_hash(user.password), role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token", response_model=schemas.Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid creds")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/resources", response_model=List[schemas.ResourceOut], tags=["Resources"])
def get_resources(db: Session = Depends(database.get_db)):
    return db.query(models.Resource).all()


@app.post("/bookings", response_model=schemas.BookingOut, tags=["Bookings"])
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(database.get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    if booking.start_time >= booking.end_time:
        raise HTTPException(status_code=400, detail="Invalid interval")

    overlap = db.query(models.Booking).filter(
        models.Booking.resource_id == booking.resource_id,
        models.Booking.start_time < booking.end_time,
        models.Booking.end_time > booking.start_time
    ).first()

    if overlap:
        raise HTTPException(status_code=400, detail="Time slot taken")

    new_booking = models.Booking(**booking.model_dump(), user_id=current_user.id)
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


@app.get("/bookings/my", response_model=List[schemas.BookingOut], tags=["Bookings"])
def get_my_bookings(current_user: models.User = Depends(auth.get_current_user)):
    return current_user.bookings