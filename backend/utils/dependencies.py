from fastapi import Header
import jwt
from jwt.exceptions import (
    InvalidTokenError,
    DecodeError,
    InvalidSignatureError,
    ExpiredSignatureError,
    InvalidIssuedAtError,
    InvalidKeyError,
    InvalidAlgorithmError,
    MissingRequiredClaimError,
)
from pydantic import BaseModel

from ..config import config
from .exception import UnicornException


async def token_jwt(
    Authorization: str = Header()
):
    try:
        token = Authorization.split("Bearer ")[1]
        t = jwt.decode(token, config.conf.JWT_SECRET, algorithms=["HS256"])
        return t

    except (
        InvalidTokenError,
        DecodeError,
        InvalidSignatureError,
        ExpiredSignatureError,
        InvalidIssuedAtError,
        InvalidKeyError,
        InvalidAlgorithmError,
        MissingRequiredClaimError,
        IndexError
    ):
        raise UnicornException(
            status=404, 
            message="JWT Error!"
        )


class Item(BaseModel):
    refresh_token: str


async def refresh_token(
    item: Item
):
    try:
        t = jwt.decode(
            item.refresh_token, 
            config.conf.JWT_SECRET, 
            algorithms=["HS256"]
        )
        return t

    except (
        InvalidTokenError,
        DecodeError,
        InvalidSignatureError,
        ExpiredSignatureError,
        InvalidIssuedAtError,
        InvalidKeyError,
        InvalidAlgorithmError,
        MissingRequiredClaimError
    ):
        raise UnicornException(
            status=404, 
            message="Refresh JWT Error!"
        )


async def refresh_token_get(
    refresh_token: str
):
    try:
        t = jwt.decode(
            refresh_token, 
            config.conf.JWT_SECRET, 
            algorithms=["HS256"]
        )
        return t

    except (
        InvalidTokenError,
        DecodeError,
        InvalidSignatureError,
        ExpiredSignatureError,
        InvalidIssuedAtError,
        InvalidKeyError,
        InvalidAlgorithmError,
        MissingRequiredClaimError
    ):
        raise UnicornException(
            status=404, 
            message="Refresh JWT Error!"
        )
