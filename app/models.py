from sqlalchemy import Column, Integer, String, DateTime, LargeBinary
from sqlalchemy.sql import text
from database import Base
from sqlalchemy.sql.sqltypes import TIMESTAMP

class TaskDB(Base):

    __tablename__ = "tasks"

    task_id = Column(Integer,primary_key=True, autoincrement=True, nullable=False)
    name = Column(String,nullable=False)
    description = Column(String,nullable=True)
    status = Column(String, server_default='pending')
    due_date = Column(DateTime, server_default = text("NOW() + INTERVAL'7 day'"))
    completed_date = Column(DateTime)
    assigned_to = Column(String,nullable=True)
    priority = Column(String,server_default='medium')



class User(Base):

    __tablename__ = "users"

    id = Column(Integer,primary_key=True, autoincrement=True, nullable=False)
    email = Column(String, nullable=False,unique=True)
    password = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP(timezone = True), nullable=False, server_default=text('now()'))