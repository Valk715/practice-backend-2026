from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
from . import models, schemas, auth, database

app = FastAPI(title="Booking API Pro")

@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=database.engine)

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(400, "Email registered")
    new_user = models.User(email=user.email, hashed_password=auth.get_password_hash(user.password), role=user.role)
    db.add(new_user); db.commit(); db.refresh(new_user)
    return new_user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": auth.create_access_token({"sub": user.email}), "token_type": "bearer"}

@app.get("/resources")
def get_resources(
    cat: Optional[str] = None,
    cap: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    q = db.query(models.Resource)
    if cat: q = q.filter(models.Resource.category == cat)
    if cap: q = q.filter(models.Resource.capacity >= cap)
    res = q.all()
    out = []
    for r in res:
        avg = db.query(func.avg(models.Review.rating)).filter(models.Review.resource_id == r.id).scalar() or 0
        out.append({"info": r, "rating": round(float(avg), 1)})
    return out

@app.post("/resources")
def create_resource(res: schemas.ResourceCreate, db: Session = Depends(database.get_db), u: models.User = Depends(auth.get_current_user)):
    if u.role != "admin": raise HTTPException(403, "Admin only")
    new_res = models.Resource(**res.dict())
    db.add(new_res); db.commit(); db.refresh(new_res)
    return new_res

@app.post("/bookings")
def create_booking(b: schemas.BookingCreate, db: Session = Depends(database.get_db), u: models.User = Depends(auth.get_current_user)):
    overlap = db.query(models.Booking).filter(
        models.Booking.resource_id == b.resource_id,
        models.Booking.status == "active",
        models.Booking.start_time < b.end_time,
        models.Booking.end_time > b.start_time
    ).first()
    if overlap: raise HTTPException(400, "Conflict")
    new_b = models.Booking(**b.dict(), user_id=u.id)
    db.add(new_b); db.commit(); db.refresh(new_b)
    return new_b

@app.get("/bookings/my")
def my_bookings(u: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return db.query(models.Booking).filter(models.Booking.user_id == u.id).all()

@app.delete("/bookings/{id}")
def cancel_booking(id: int, db: Session = Depends(database.get_db), u: models.User = Depends(auth.get_current_user)):
    bk = db.query(models.Booking).filter(models.Booking.id == id).first()
    if not bk: raise HTTPException(404)
    if u.role != "admin" and bk.user_id != u.id: raise HTTPException(403)
    bk.status = "cancelled"; db.commit()
    return {"msg": "ok"}

@app.post("/reviews")
def leave_review(r: schemas.ReviewCreate, db: Session = Depends(database.get_db), u: models.User = Depends(auth.get_current_user)):
    done = db.query(models.Booking).filter(
        models.Booking.user_id == u.id,
        models.Booking.resource_id == r.resource_id,
        models.Booking.end_time < datetime.now()
    ).first()
    if not done: raise HTTPException(400, "Must finish booking first")
    new_r = models.Review(**r.dict(), user_id=u.id)
    db.add(new_r); db.commit(); return {"msg": "Review added"}