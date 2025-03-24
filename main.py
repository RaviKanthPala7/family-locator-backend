from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, schemas
from passlib.context import CryptContext
from models import User
from schemas import UserLogin

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm




app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

models.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ User Registration
@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(name=user.name, email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user or not user.verify_password(user_credentials.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/locations")
def add_location(location: schemas.LocationCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Store the location
    db_location = models.Location(user_id=user.id, latitude=location.latitude, longitude=location.longitude)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    
    return {"message": "Location added successfully"}


@app.get("/locations/latest", response_model=schemas.LocationResponse)
def get_latest_location(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch the latest location
    latest_location = db.query(models.Location).filter(models.Location.user_id == user.id).order_by(models.Location.timestamp.desc()).first()
    
    if latest_location is None:
        raise HTTPException(status_code=404, detail="No location data available")

    return latest_location


@app.get("/locations/history", response_model=list[schemas.LocationResponse])
def get_location_history(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch all locations for the user (most recent first)
    locations = db.query(models.Location).filter(models.Location.user_id == user.id).order_by(models.Location.timestamp.desc()).all()
    
    if not locations:
        raise HTTPException(status_code=404, detail="No location history available")

    return locations


@app.get("/locations/latest/{email}", response_model=schemas.LocationResponse)
def get_latest_location(email: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        requester = db.query(models.User).filter(models.User.email == user_email).first()
        if requester is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Find the target user
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the latest location of the user
    latest_location = (
        db.query(models.Location)
        .filter(models.Location.user_id == user.id)
        .order_by(models.Location.timestamp.desc())
        .first()
    )

    if not latest_location:
        raise HTTPException(status_code=404, detail="No location data available")

    return latest_location


@app.get("/locations/history/{email}", response_model=list[schemas.LocationResponse])
def get_location_history(email: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        requester = db.query(models.User).filter(models.User.email == user_email).first()
        if requester is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Find the target user
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all location records for the user
    locations = (
        db.query(models.Location)
        .filter(models.Location.user_id == user.id)
        .order_by(models.Location.timestamp.desc())
        .all()
    )

    if not locations:
        raise HTTPException(status_code=404, detail="No location data available")

    return locations


@app.post("/follow/{email}")
def follow_user(email: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        follower = db.query(models.User).filter(models.User.email == user_email).first()
        if follower is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Find the user to follow
    followed = db.query(models.User).filter(models.User.email == email).first()
    if not followed:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already following
    existing_follow = db.query(models.Follow).filter(
        models.Follow.follower_id == follower.id,
        models.Follow.followed_id == followed.id
    ).first()
    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")

    # Add follow relationship
    follow_entry = models.Follow(follower_id=follower.id, followed_id=followed.id)
    db.add(follow_entry)
    db.commit()

    return {"message": f"You are now following {email}"}


@app.get("/locations/{email}", response_model=schemas.LocationResponse)
def get_latest_location(email: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        requester = db.query(models.User).filter(models.User.email == user_email).first()
        if requester is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Check if requester follows the target user
    target_user = db.query(models.User).filter(models.User.email == email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    follow_entry = db.query(models.Follow).filter(
        models.Follow.follower_id == requester.id,
        models.Follow.followed_id == target_user.id
    ).first()

    if not follow_entry:
        raise HTTPException(status_code=403, detail="You are not following this user")

    # Fetch the latest location
    latest_location = (
        db.query(models.Location)
        .filter(models.Location.user_id == target_user.id)
        .order_by(models.Location.timestamp.desc())
        .first()
    )

    if not latest_location:
        raise HTTPException(status_code=404, detail="No location available")

    return latest_location


@app.get("/followed-users")
def get_followed_users(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        # Extract user email from the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch the list of followed user IDs
    followed_ids = db.query(models.Follow.followed_id).filter(models.Follow.follower_id == user.id).all()
    
    # Extract IDs from the query result
    followed_ids = [fid[0] for fid in followed_ids]

    if not followed_ids:
        return {"followed_users": []}

    # Fetch emails of followed users
    followed_users = db.query(models.User.email).filter(models.User.id.in_(followed_ids)).all()

    # Convert result to a list of emails
    followed_emails = [user[0] for user in followed_users]

    return {"followed_users": followed_emails}
