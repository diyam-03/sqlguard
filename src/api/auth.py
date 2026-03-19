import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from src.db_connect import get_connection

# Secret key — change this in production
SECRET_KEY = "sqlguard_secret_key_2025_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365  # 1 year

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# ─── PYDANTIC MODELS ───

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserRegister(BaseModel):
    username: str
    password: str
    role: Optional[str] = "viewer"
    ip_address: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# ─── HELPER FUNCTIONS ───

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_from_db(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, username, password_hash, role, is_active 
        FROM users WHERE username = %s
    """, (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user_from_db(token_data.username)
    if user is None:
        raise credentials_exception
    return user