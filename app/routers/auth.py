from fastapi import APIRouter, Depends, status, HTTPException, Response
from database import get_db
from schemas import Token
from sqlalchemy.orm import Session
from models import User
from utils import verify
from oauth2 import create_access_token
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter(tags=['Auth'], prefix="/login")

@router.post('/', response_model = Token)
def login(user_cred : OAuth2PasswordRequestForm = Depends(), 
          db : Session = Depends(get_db)):
    
    try:
        user = db.query(User).filter(User.email == user_cred.username).first()

        
        if not user or not verify(user_cred.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Invalid Credentials"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid Credentials"
        )
    
    access_token = create_access_token(data={"id":user.id})

    return {"access_token" : access_token,
            "token_type" : "bearer"}

