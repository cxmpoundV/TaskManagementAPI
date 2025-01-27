from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHMEY_DATABASE_URL = 'postgresql://postgres:6625099@localhost/postgres'


engine  = create_engine(SQLALCHMEY_DATABASE_URL)

SessionLocal =  sessionmaker(autocommit = False ,autoflush = False, bind = engine)

Base = declarative_base()

def get_db():
    
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


