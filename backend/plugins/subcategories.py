from fastapi import APIRouter, Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from ..database import Subcategories
from ..utils import TokenJwt, UnicornException, roles, token_jwt


router = APIRouter(
    prefix="/subcategories",
    tags=["subcategories"]
)


# all: get subcategories
@router.get("/")
async def get_subcategories(
    token: TokenJwt = Depends(token_jwt)
):
    categories = await Subcategories.all().order_by("order").values()

    return {
        "error": False,
        "message": "",
        "categories": categories
    }


# all: get list subcategories
@router.get("/list")
async def get_list_subcategories(
    token: TokenJwt = Depends(token_jwt)
):
    categories = [x["name"] for x in await Subcategories.all().values()]

    return {
        "error": False,
        "message": "",
        "categories": categories
    }


class AddSubcategoriesItem(BaseModel):
    name: str
    order: int


# admin: add subcategory
@router.post("/")
@roles("admin")
async def add_subcategory(
    item: AddSubcategoriesItem,
    token: TokenJwt = Depends(token_jwt)
):
    if not item.name:
        raise UnicornException(
            status=400,
            message="Name missed"
        )

    try:
        await Subcategories(name=item.name, order=item.order).save()
    except IntegrityError:
        raise UnicornException(
            status=400,
            message="Existing subcategories"
        )
    
    return {"error": False, "message": ""}


#admin: delete category
@router.delete("/{subcategory_id}")
@roles("admin")
async def delete_subcategory(
    subcategory_id: int,
    token: TokenJwt = Depends(token_jwt)
):
    subcategory = Subcategories.filter(id=subcategory_id)

    if not await subcategory.exists():
        raise UnicornException(
            status=404,
            message="Subcategory not exist"
        )
    
    await subcategory.delete()

    return {"error": False, "message": ""}
