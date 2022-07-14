from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends
from argon2.exceptions import (
    VerificationError,
    VerifyMismatchError,
    HashingError,
    InvalidHash
)
import jwt
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from ..config import config
from ..database import Users
from ..utils import UnicornException, token_jwt, refresh_token, roles


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
                "role": user["role"]
            }, 
            config.conf.JWT_SECRET,
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc)+timedelta(seconds=60*60),
                "username": username,
                "role": user["role"]
            },
            config.conf.JWT_SECRET,
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
    token: dict = Depends(token_jwt)
):
    if item.role not in config.conf.ROLES:
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
    refresh_token: dict = Depends(refresh_token)
):
    user = await Users.get(username=refresh_token["username"])

    try:
        ph = PasswordHasher()
        ph.verify(user.password, item.password)

        token = jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc)+timedelta(seconds=60*15),
                "username": refresh_token["username"],
                "role": user.role
            }, 
            config.conf.JWT_SECRET,
            algorithm="HS256"
        )

        return {
            "error": False,
            "message": "",
            "token": token
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
