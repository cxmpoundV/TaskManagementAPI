from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, Union
from datetime import datetime

class TaskModel(BaseModel):
    task_id: int
    name: str
    description: Union[str, None]
    status: str
    due_date: datetime
    completed_date: Optional[datetime] = None
    assigned_to: Union[str, None]
    priority: Optional[str] = "medium"

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

    class ConfigDict:
        from_attributes=True


class TaskCreate(BaseModel):
    
    name: str
    status: str
    due_date: datetime


class UpdateStatus(BaseModel):
    task_id: int
    status: str


class UpdateDueDate(BaseModel):
    task_id: int
    due_date: datetime


class UserCreate(BaseModel):
    email : EmailStr
    password : str


class UserResponse(BaseModel):
    id : int
    email : EmailStr
    created_at : str

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class UserLogin(BaseModel):
    email : EmailStr
    password : str

class Token(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    id : Optional[int] = None
