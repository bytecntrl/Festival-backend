from typing import Dict, List, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from schema import Schema
from tortoise.exceptions import IntegrityError

from ..config import config
from ..database import Products, RoleProduct, Subcategories, Variant
from ..utils import (
    Category, 
    TokenJwt, 
    UnicornException,
    refresh_token, 
    roles, 
    token_jwt
)


router = APIRouter(
    prefix="/products",
    tags=["products"]
)


SCHEMA_ROLE = Schema(config.conf.ROLES)
SCHEMA_VARIANT = Schema([{"name": str, "price": float}])


# all: get all products
@router.get("/")
async def get_products(
    token: TokenJwt = Depends(refresh_token)
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
    subcategory: str
    roles: List[str]
    variant: List[Dict[str, Union[str, float]]]

    class Config:
        smart_union = True


# admin: add product
@router.post("/")
@roles("admin")
async def add_product(
    item: AddProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    if not item.name:
        raise UnicornException(
            status=400,
            message="Wrong name"
        )
    if item.price <= 0:
        raise UnicornException(
            status=400,
            message="Wrong price"
        )
    if not SCHEMA_ROLE.is_valid(item.roles):
        raise UnicornException(
            status=400,
            message="Wrong roles schema"
        )
    if not SCHEMA_VARIANT.is_valid(item.variant):
        raise UnicornException(
            status=400,
            message="Wrong variant schema"
        )

    try:
        s = await Subcategories.get_or_none(name=item.subcategory)
        if not s:
            raise UnicornException(
                status=400,
                message="subcategory nonexistent"
            )

        p = await Products.create(
            name=item.name,
            price=item.price,
            category=item.category.value,
            subcategory=s
        )

        for x in item.roles:
            await RoleProduct(role=x, product=p).save()

        for y in item.variant:
            await Variant(name=y["name"], price=y["price"], product=p).save()

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
    token: TokenJwt = Depends(token_jwt)
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
