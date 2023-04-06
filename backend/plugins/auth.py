from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    HashingError, 
    InvalidHash, 
    VerificationError,
    VerifyMismatchError
)
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from ..config import Session
from ..database import Users
from ..utils import TokenJwt, UnicornException, refresh_token, roles, token_jwt


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.get("/")
async def login(
    username: str,
    password: str
):
    user = await Users.get_or_none(username=username).values()

    if not user:
        raise UnicornException(
            status=404,
            message="Invalid username or password"
        )
    
    try:
        ph = PasswordHasher()
        ph.verify(user["password"], password)

        token = jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc)+timedelta(seconds=60*15),
                "username": username,
                "role": user["role"],
                "type": "access"
            }, 
            Session.config.JWT_SECRET,
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc)+timedelta(seconds=60*60),
                "username": username,
                "role": user["role"],
                "type": "refresh"
            },
            Session.config.JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "error": False,
            "message": "",
            "token": token,
            "refresh_token": refresh_token
        }
    except (
        VerificationError,
        VerifyMismatchError,
        HashingError,
        InvalidHash
    ):
        raise UnicornException(
            status=404,
            message="Invalid username or password"
        )


class RegisterItem(BaseModel):
    username: str
    password: str
    role: str


# admin: add new user
@router.post("/")
@roles("admin")
async def register(
    item: RegisterItem,
    token: TokenJwt = Depends(token_jwt)
):
    if item.role not in Session.config.ROLES:
        raise UnicornException(
            status=404,
            message="Non-existent role"
        )

    try:
        ph = PasswordHasher()

        await Users(
            username=item.username,
            password=ph.hash(item.password),
            role=item.role
        ).save()

        return {
            "error": False,
            "message": ""
        }
    except IntegrityError:
        raise UnicornException(
            status=400,
            message="User alredy exists"
        )


class TokenItem(BaseModel):
    password: str


# all: generate new access token
@router.post("/token")
async def new_token(
    item: TokenItem,
    token: TokenJwt = Depends(refresh_token)
):
    user = await Users.get(username=token.username)

    try:
        ph = PasswordHasher()
        ph.verify(user.password, item.password)

        access_token = jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc)+timedelta(seconds=60*15),
                "username": token.username,
                "role": user.role,
                "type": "access"
            }, 
            Session.config.JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "error": False,
            "message": "",
            "token": access_token
        }
    except (
        VerificationError,
        VerifyMismatchError,
        HashingError,
        InvalidHash
    ):
        raise UnicornException(
            status=404,
            message="Invalid password"
        )
