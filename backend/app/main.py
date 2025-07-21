import os
from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from stockfish import Stockfish
from sqlalchemy.orm import Session
from sqlalchemy import exc # For handling database exceptions
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta

# Import database and models
from .database import SessionLocal, engine, get_db, Base
from . import models

# For password hashing
from passlib.context import CryptContext

# For JWT (JSON Web Tokens)
from jose import JWTError, jwt

# Load .env from /backend/
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# --- Security Constants ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # can change later

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# Create database tables on startup (for development purposes)
# In production, you'd typically use Alembic for migrations
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/checked.")

stockfish = Stockfish(path="./stockfish/stockfish")

class PlayRequest(BaseModel):
    fen: str
    user_move: str

class UserIn(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserOut(BaseModel):
    email: EmailStr
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Helper Functions for Security ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})  # Add expiration to token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Authentication Endpoints ---

@app.post("/signup", response_model=UserOut)
async def signup(user: UserIn, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    
    # Create a new user object
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user) # Refresh to get the generated ID
        return UserOut(email=new_user.email, name=new_user.name)
    except exc.SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during signup: {e}")


@app.post("/login", response_model=Token)
async def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/move")
def get_best_move(fen: str = Query(..., description="FEN position before the user move")):
    stockfish.set_fen_position(fen)
    return {"best_move": stockfish.get_best_move()}

@app.get("/evaluate")
def evaluate_position(fen: str = Query(..., description="FEN string representing the position")):
    stockfish.set_fen_position(fen)
    evaluation = stockfish.get_evaluation()
    print(evaluation)
    if evaluation["type"] == "cp":
        score = round(evaluation["value"] / 100, 2)
        return JSONResponse(content={"evaluation": f"{score}"})
    elif evaluation["type"] == "mate":
        return JSONResponse(content={"evaluation": f"Mate in {evaluation['value']}"})
    else:
        return JSONResponse(content={"error": "Unknown evaluation type"}, status_code=500)
    
@app.get("/feedback")
def get_feedback(
    fen: str = Query(..., description="FEN position before the user move"),
    user_move: str = Query(..., description="User move in UCI format (e.g., e2e4)")
):
    # Set the initial position
    stockfish.set_fen_position(fen)

    # Get Stockfish's best move from this position
    best_move = stockfish.get_best_move()

    # Evaluate the position *before* the move
    base_eval = stockfish.get_evaluation()

    # Apply user move
    if not stockfish.is_move_correct(user_move):
        return JSONResponse(content={"error": "Illegal move"}, status_code=400)

    stockfish.make_moves_from_current_position([user_move])
    user_eval = stockfish.get_evaluation()

    # Revert back for safety (optional but clean)
    stockfish.set_fen_position(fen) # MAYBE ILL CHANGE THIS IN THE FUTURE

    def get_score(eval):
        if eval["type"] == "cp":
            return eval["value"]
        elif eval["type"] == "mate":
            return 10000 if eval["value"] > 0 else -10000
        else:
            return 0

    base_score = get_score(base_eval)
    user_score = get_score(user_eval)
    delta = user_score - base_score

    # Interpretation
    diff = abs(delta)
    if diff <= 20:
        verdict = "Excellent"
    elif diff <= 50:
        verdict = "Good"
    elif diff <= 150:
        verdict = "Inaccuracy"
    elif diff <= 300:
        verdict = "Mistake"
    else:
        verdict = "Blunder"

    return {
        "base_score": get_score(base_eval),
        "user_score":get_score(user_eval),
        "best_move": best_move,
        "user_move": user_move,
        "score_diff": round(delta / 100, 2),
        "feedback": verdict
    }

@app.post("/play")
def play_move(data: PlayRequest):
    # Set up position
    if not stockfish.is_fen_valid(data.fen):
        raise HTTPException(status_code=400, detail="Invalid FEN")

    stockfish.set_fen_position(data.fen)

    # Make user's move
    if not stockfish.is_move_correct(data.user_move):
        raise HTTPException(status_code=400, detail="Invalid user move")

    stockfish.make_moves_from_current_position([data.user_move])

    # Engine's move
    engine_move = stockfish.get_best_move()
    if engine_move is None:
        return {
            "user_move": data.user_move,
            "engine_move": None,
            "message": "Game over or no legal move.",
            "updated_fen": stockfish.get_fen_position()
        }

    stockfish.make_moves_from_current_position([engine_move])

    return {
        "user_move": data.user_move,
        "engine_move": engine_move,
        "updated_fen": stockfish.get_fen_position()
    }