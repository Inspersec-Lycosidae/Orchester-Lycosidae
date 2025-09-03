# database.py
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from models import Base

#Read from environment (Docker provides it) - No use for python-dotenv (only if local .env)
#URL Structure: <Database>+<Connector>://{username}:{password}@{host}:{port}/{database_name}
#Example URL: mariadb+pymysql://user:password@db_host:3306/database_name
#Example URL: mariadb+mariadbconnector://user:password@db_host:3306/database_name
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Environment variable DATABASE_URL is not set.")

#Create SQLAlchemy engine
#Uses retry to try connecting to db (1o times with 3 seconds interval)
#Prevents race condition on docker-compose and other paralelisms
for _ in range(10):
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            echo=True,
        )
        connection = engine.connect()
        connection.close()
        break
    except OperationalError:
        print("Database not ready, retrying in 3 seconds...")
        time.sleep(3)
else:
    raise RuntimeError("Database connection failed after retries.")

#Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

#Initialize DB tables
def init_db():
    Base.metadata.create_all(bind=engine)

#Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
