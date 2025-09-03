#middleware.py
#Functions that are ran before the calling of my authenticated routes, for veryfying the
#session token and extracting its info for use in the routes functions
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from schemas import AuthToken
from typing import Dict
import jwt
import os

#Read from environment (Docker provides it) - No use for python-dotenv (only if local .env)
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("Environment variable JWT_SECRET is not set.")
#JWT_EXPIRATION is given in seconds as by JWT standard (Unix timestamp (int) )
JWT_EXPIRATION = os.getenv("JWT_EXPIRATION")
if not JWT_EXPIRATION:
    JWT_EXPIRATION = 1800
elif type(JWT_EXPIRATION) == str:
    try:
        JWT_EXPIRATION = int(JWT_EXPIRATION)
    except:
        raise RuntimeError("Environment variable JWT_EXPIRATION is not properly set.")

#Sets the defaults for cookie-reading and veryfing; mutable depending on the application
ALGORITHM = "HS256"
COOKIE_NAME = "session_token"

######################################################
### Helper Function to extract token from a Bearer ###
######################################################

#Extract JWT from cookie or Authorization header
#Input: http/https request
#Output: String of the token
def extract_token(request: Request) -> str:
    # First try cookie
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    #Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()
    raise HTTPException(status_code=401, detail="User not authenticated")

#Description: Receives a http/https request and returns the session_token JWT as a Python Dictionary
#Input: http/https request
#Output: Python Dict object
def get_cookie_as_dict(request: Request) -> Dict:
    token = extract_token(request)

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

#Description: Receives a http/https request and returns the session_token JWT as a AuthToken object
#Input: http/https request
#Output: AuthToken object
def get_cookie_as_model(request: Request) -> AuthToken:
    payload = get_cookie_as_dict(request)
    try:
        return AuthToken(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token payload invalid: {e}")
    

#Description: Receives a python dictionary and returns a valid JWT token string
#Input: Python Dictionary
#Output: JWT String
def make_cookie_from_dict(payload: Dict) -> str:
    payload = payload.copy()

    expire = datetime.now(datetime.timezone.utc) + timedelta(seconds=JWT_EXPIRATION)
    payload["exp"] = int(expire.timestamp())

    try:
        token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
        return token
    except Exception as e:
        raise RuntimeError(f"Error generating token: {e}")
    

#Description: Receives a AuthToken object and returns a valid JWT token string
#Input: AuthToken Object
#Output: JWT String
def make_cookie_from_model(auth_token: AuthToken) -> str:
    payload = auth_token.dict(exclude_none=True)
    return make_cookie_from_dict(payload)