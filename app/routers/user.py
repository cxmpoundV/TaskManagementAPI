from fastapi import Depends, HTTPException, status, APIRouter, Response
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserCreate,UserResponse
from models import User
import logging
from typing import List
from utils import hash_password


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"],prefix="/users")

@router.get("/",status_code=status.HTTP_200_OK, response_model = List[UserResponse])
def get_users(db: Session = Depends(get_db)):

    try:
        users = db.query(User).all()
        return [
            UserResponse(
                id=user.id,
                email=user.email,
                created_at=user.created_at.isoformat()
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred"
        )

@router.post("/",status_code=status.HTTP_201_CREATED,response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    #hash the pass
    hash_pass = hash_password(user.password)
    user.password = hash_pass

    try:

        new_user = User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "id": new_user.id,
            "email": new_user.email,
            "created_at": new_user.created_at.isoformat() 
        }
    
    except Exception as e:

        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{id}",status_code=status.HTTP_200_OK, response_model=UserResponse)
def get_user_by_id(id : int, db : Session = Depends(get_db)):

    try:

        user = db.query(User).filter(User.id == id).first()
        return {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }

    except Exception as e:
        logger.error(f"Error Finding the error : {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User Not Found")

   