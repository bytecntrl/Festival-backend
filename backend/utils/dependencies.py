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
    access_token: str = Header(alias="Authorization")
):
    try:
        token = access_token.split("Bearer ")[1]
        return jwt.decode(token, config.conf.JWT_SECRET, algorithms=["HS256"])

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


async def refresh_token(
    refresh_token: str = Header(alias="Authorization")
):
    try:
        token = refresh_token.split("Bearer ")[1]
        return jwt.decode(token, config.conf.JWT_SECRET, algorithms=["HS256"])

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
            message="Refresh JWT Error!"
        )
