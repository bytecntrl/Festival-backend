import datetime
import string

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
from ..utils.enums import Roles


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
    role: Roles


# admin: add new user
@router.post("/")
@roles("admin")
async def register(
    item: RegisterItem,
    token: TokenJwt = Depends(token_jwt)
):
    if item.role.value == "admin":
        raise UnicornException(
            status=404,
            message="Unable to create admin user"
        )

    if not item.username or not item.password:
        raise UnicornException(
            status=400,
            message="User or password missed"
        )
    
    if not all(map(lambda x: x in string.ascii_letters, item.username)):
        raise UnicornException(
            status=400,
            message="The username has illegal characters"
        )

    if len(item.password) >= 29 or len(item.username) >= 29:
        raise UnicornException(
            status=400,
            message="User or password too long"
        )

    try:
        ph = PasswordHasher()

        await Users(
            username=item.username,
            password=ph.hash(item.password),
            role=item.role.value
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
