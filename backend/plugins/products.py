from unicodedata import category
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from tortoise.exceptions import IntegrityError

from ..database import Products
from ..utils import (
    Category,
    refresh_token_get,
    roles, 
    token_jwt, 
    UnicornException
)


router = APIRouter(
    prefix="/products",
    tags=["products"]
)


# all: get all products
@router.get("/")
async def get_products(
    refresh_token: dict = Depends(refresh_token_get)
):
    p = await Products.all().values()

    return {
        "error": False,
        "message": "",
        "products": p
    }


class AddProductItem(BaseModel):
    name: str
    price: float
    category: Category


# admin: add product
@router.post("/")
@roles("admin")
async def add_product(
    item: AddProductItem,
    token: dict = Depends(token_jwt)
):
    if item.price <= 0:
        raise UnicornException(
            status=400,
            message="Wrong price"
        )

    try:
        await Products(
            name=item.name,
            price=item.price,
            category=item.category.value
        ).save()

        return {
            "error": False,
            "message": ""
        }
    except IntegrityError:
        raise UnicornException(
            status=400,
            message="existing product"
        )


class DeleteProductItem(BaseModel):
    name: str


# admin: delete product
@router.delete("/")
@roles("admin")
async def delete_product(
    item: DeleteProductItem,
    token: dict = Depends(token_jwt)
):
    product = Products.filter(name=item.name)

    if not await product.exists():
        raise UnicornException(
            status=404,
            message="product not exist"
        )
    
    await product.delete()

    return {
        "error": False,
        "message": ""
    }
