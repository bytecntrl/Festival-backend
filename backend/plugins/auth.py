import datetime

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
from ..utils import TokenJwt, UnicornException, roles, token_jwt


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
    
    exp = (
        datetime.datetime.now(tz=datetime.timezone.utc) + 
        datetime.timedelta(seconds=Session.config.JWT_TOKEN_EXPIRES)
    )

    token = jwt.encode(
        {
            "exp": exp,
            "username": username,
            "role": user["role"]
        }, 
        Session.config.JWT_SECRET,
        algorithm="HS256"
    )

    return {
        "error": False,
        "message": "",
        "token": token
    }


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

    if item.password >= 29 or item.username >= 29:
        raise UnicornException(
            status=400,
            message="User or password too long"
        )

    try:
        ph = PasswordHasher()

        await Users(
            username=item.username,
            password=ph.hash(item.password),
            role=item.role
        ).save()

    except IntegrityError:
        raise UnicornException(
            status=400,
            message="User alredy exists"
        )
    
    return {
        "error": False,
        "message": ""
    }
