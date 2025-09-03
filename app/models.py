# models.py
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Time, ForeignKey, CheckConstraint, UniqueConstraint, SmallInteger
)
from sqlalchemy.orm import relationship, declarative_base
Base = declarative_base()

######################################################################
##### Uses SqlAlchemy bases for static objects; referenced in DB #####
######################################################################

#Default password table for saving the user password as a hash256
#(Receives the hashed string)
class Password(Base):
    __tablename__ = 'password'

    id = Column(Integer, primary_key=True, autoincrement=True)
    password256 = Column(String(256), nullable=False)

#Default generic user table
#Use for reference on developing new tables
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(60), nullable=False, unique=True)
    email = Column(String(45), nullable=False, unique=True)
    id_password = Column(Integer, ForeignKey('password.id'))

    password = relationship("Password")

    __table_args__ = (
        UniqueConstraint('id_password'),
    )
