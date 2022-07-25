from argon2 import PasswordHasher
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..database import Users
from ..utils import TokenJwt, UnicornException, refresh_token, roles, token_jwt


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


# admin: get list of user
@router.get("/")
@roles("admin")
async def get_users(
    token: TokenJwt = Depends(refresh_token)
):
    users = Users.all()
    us = users.exclude(username=token.username)

    return {
        "error": False,
        "message": "",
        "users": await us.values("id", "username", "role")
    }


# all: get user information
@router.get("/{username}")
async def get_user_admin(
    username: str,
    token: TokenJwt = Depends(refresh_token)
):
    user = await Users.get_or_none(username=username)

    if not user:
        raise UnicornException(
            status=404,
            message="Invalid username"
        )

    if (
        not(
            token.role == "admin" or 
            token.username == username
        )
    ):
        raise UnicornException(
            status=405,
            message="not allowed"
        )

    return {
        "error": False,
        "message": "",
        "user": await user.to_dict()
    }


class ChangePasswordItem(BaseModel):
    password: str


# all: change password of user
@router.put("/")
async def change_password(
    item: ChangePasswordItem,
    token: TokenJwt = Depends(token_jwt)
):
    ph = PasswordHasher()

    await Users.filter(username=token.username).update(
        password=ph.hash(item.password)
    )

    return {
        "error": False,
        "message": ""
    }


class DeleteUserItem(BaseModel):
    username: str


# admin: delete user
@router.delete("/")
@roles("admin")
async def delete_user(
    item: DeleteUserItem,
    token: TokenJwt = Depends(token_jwt)
):
    user = Users.filter(username=item.username)

    if not await user.exists():
        raise UnicornException(
            status=404,
            message="user not exist"
        )

    await user.delete()

    return {
        "error": False,
        "message": ""
    }
