from typing import List

from fastapi import APIRouter, Depends, HTTPException, Form,status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError

from project.app.schemas import schemas
from project.app.crud import crud
from project.dependencies import get_db
from project.app.utils import utils as auth_utils

from fastapi.security import (
    # HTTPBearer,
    # HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
)

router = APIRouter(prefix='/jwt', tags=["sign"])

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="jwt/login/",
)

def validate_auth_user(
    # user_name: str = Form(),
    # password: str = Form(),
    u: schemas.Signin,
    db: Session = Depends(get_db)
) -> schemas.UserBase:
    print("user_name:",u.user_name ,"   pwd:",u.password)
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid username or password",
    )
    if not (user := crud.get_user_by_name(db=db, user_name=u.user_name)):
        raise unauthed_exc

    if not auth_utils.validate_password(
        password=u.password,
        hashed_password=user.hashed_password,
    ):
        raise unauthed_exc

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user inactive",
        )

    return user





@router.post("/signup", response_model=dict)
async def create_user(
    user: schemas.UserBase ,
    db: Session = Depends(get_db)
):

    if crud.user_check(db= db,user_name = user.user_name) :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user already registered")


    hashed_password = auth_utils.hash_password(user.password)

    response = crud.create_user(db=db ,user_name=user.user_name, name=user.name,phone_number = user.phone_number,email=user.email,hashed_password=hashed_password,active=user.active)

    return {"message": f" add user successfully {response.user_name}"}



@router.post("/login/", response_model=schemas.TokenInfo)
def auth_user_issue_jwt(
    user: schemas.UserBase   = Depends(validate_auth_user),
):

    jwt_payload = {
        # subjec
        "sub": user.user_name,
        "username": user.user_name,
        "phonenumber":user.phone_number,
        "email": user.email,
        # "logged_in_at"
    }

    token = auth_utils.encode_jwt(jwt_payload)

    return schemas.TokenInfo(
        access_token=token,
        token_type="Bearer",
    )

def get_current_token_payload(
    # credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    token: str = Depends(oauth2_scheme),
) -> dict:
    # token = credentials.credentials
    try:
        payload = auth_utils.decode_jwt(
            token=token,
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token error: {e}",
            # detail=f"invalid token error",
        )
    return payload

def get_current_auth_user(
    payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
) -> schemas.UserBase:
    user_name: str | None = payload.get("sub")
    if user := crud.get_user_by_name(db= db, user_name= user_name):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )

def get_current_active_auth_user(
    user: schemas.UserBase = Depends(get_current_auth_user),
):
    if user.active:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="user inactive",
    )



@router.get("/users/me/")
def auth_user_check_self_info(
    payload: dict = Depends(get_current_token_payload),
    user: schemas.UserBase = Depends(get_current_active_auth_user),
):
    iat = payload.get("iat")
    return {
        "owner_id": user.id,
        "username": user.user_name,
        "name" : user.name,
        "email": user.email,
        "logged_in_at": iat,
    }