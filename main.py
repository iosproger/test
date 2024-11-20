
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware

from crud import create_user, authenticate_user, get_user_by_email
from database import SessionLocal, get_db

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000",
    "http://localhost:3000",  # Common React dev server port
    "http://localhost:5173",  # Add this line for Vite
    "http://192.168.138.69",  # Add this line for your backend IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret key for session management
SECRET_KEY = "your-secret-key"
TOKEN_EXPIRATION = 86400

# Middleware for session management
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeTimedSerializer(SECRET_KEY)


class SignUpSchema(BaseModel):
    email: str
    password: str


@app.post("/signup")
def sign_up(user: SignUpSchema, db: SessionLocal = Depends(get_db)):
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already registered")

    hashed_password = pwd_context.hash(user.password)
    create_user(db, email=user.email, hashed_password=hashed_password)
    return {"message": "User created successfully!"}


@app.post("/signin")
def sign_in(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: SessionLocal = Depends(get_db),
):
    print(form_data.username," " , form_data.password)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = serializer.dumps(user.email)
    response.set_cookie(key="session", value=token, httponly=True, max_age=TOKEN_EXPIRATION)
    return {"message": "Logged in successfully!"}


@app.post("/logout")
def log_out(response: Response):
    response.delete_cookie("session")
    return {"message": "Logged out successfully!"}


@app.get("/profile")
def profile(request: Request):
    session_token = request.cookies.get("session")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        email = serializer.loads(session_token, max_age=TOKEN_EXPIRATION)
    except Exception:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return {"email": email}

if __name__ == '__main__':
     uvicorn.run("main:app", reload=True, host="0.0.0.0")