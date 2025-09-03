from sqlalchemy.orm import Session
from models import *
from schemas import *
import hashlib
import os

PASS_SALT=os.getenv("PASS_SALT")
if PASS_SALT is None:
    raise ValueError("Environment variable PASS_SALT is not set.")

#Function to get all users by their email
#Input: Email string
#Output: A user DTO
def get_user_by_email(db: Session, email: str) -> UserReadDTO:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return UserReadDTO(id=user.id, username=user.username, email=user.email)
    return None

#Function to get all users by their username
#Input: USername string
#Output: A user DTO
def get_user_by_username(db: Session, username: str) -> UserReadDTO:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return UserReadDTO(id=user.id, username=user.username, email=user.email)
    return None

#Function to hash a password using hash 256 (no extra safety as argon2)
#Input: password string
#Output: hashed password string
def pass_hasher(password : str) -> str:
    hasher = hashlib.sha256()
    hasher.update((password + PASS_SALT).encode('utf-8'))
    return hasher.hexdigest()

#Function to create a generic user by DTOs
#Input: UserCreateDTO
#Output: UserReadDTO
def create_user(db: Session, userDTO: UserCreateDTO) -> UserReadDTO:
    #Hash password
    hashed_password = pass_hasher(userDTO.password)

    #Add password to db
    password = Password(password256=hashed_password)
    db.add(password)
    db.commit()
    db.refresh(password)

    #Add user to db
    user = User(
        username=userDTO.username,
        email=userDTO.email,
        id_password=password.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserReadDTO(id=user.id, username=user.username, email=user.email)