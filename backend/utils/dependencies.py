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

from ..config import Session
from .exception import UnicornException
from .token import TokenJwt


async def token_jwt(
    access_token: str = Header(alias="Authorization")
):
    try:
        token = access_token.split("Bearer ")[1]
        d = TokenJwt(**jwt.decode(
            token, 
            Session.config.JWT_SECRET, 
            algorithms=["HS256"]
        ))

        return d

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
            status=401, 
            message="JWT Error!"
        )


async def refresh_token(
    refresh_token: str = Header(alias="Authorization")
):
    try:
        token = refresh_token.split("Bearer ")[1]
        d = TokenJwt(**jwt.decode(
            token, 
            Session.config.JWT_SECRET, 
            algorithms=["HS256"]
        ))

        if d.type != "refresh":
            raise UnicornException(
                status=400,
                message="Not refresh token!"
            )

        return d

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
            status=401, 
            message="Refresh JWT Error!"
        )
