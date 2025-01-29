from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()


SQLALCHMEY_DATABASE_URL = os.getenv("SQLALCHMEY_DATABASE_URL")


engine  = create_engine(SQLALCHMEY_DATABASE_URL)

SessionLocal =  sessionmaker(autocommit = False ,autoflush = False, bind = engine)

Base = declarative_base()

def get_db():
    
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


