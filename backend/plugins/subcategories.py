from fastapi import APIRouter, Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from ..database import Subcategories
from ..utils import TokenJwt, UnicornException, roles, token_jwt


router = APIRouter(
    prefix="/subcategories",
    tags=["subcategories"]
)


class AddSubcategoriesItem(BaseModel):
    name: str
    order: int


# admin: add subcategories
@router.post("/")
@roles("admin")
async def add_subcategories(
    item: AddSubcategoriesItem,
    token: TokenJwt = Depends(token_jwt)
):
    try:
        await Subcategories(name=item.name, order=item.order).save()

        return {"error": False, "message": ""}
    except IntegrityError:
        raise UnicornException(
            status=400,
            message="existing subcategories"
        )
