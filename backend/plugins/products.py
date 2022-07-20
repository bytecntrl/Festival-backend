from collections import defaultdict
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
    product = {
        "foods": defaultdict(dict),
        "drinks": defaultdict(dict)
    }

    p = await Products.all().values()

    for x in p:
        category = await Subcategories.get(id=x["subcategory_id"])
        product[x["category"]][category.name] = x

    return {
        "error": False,
        "message": "",
        "products": {
            k: dict(v)
            for k, v in product.items()
        }
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


class AddRoleProductItem(BaseModel):
    role: str


# admin: add role to product
@router.post("/{product_id}/role")
@roles("admin")
async def add_role_product(
    product_id: int,
    item: AddRoleProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    if item.role not in config.conf.ROLES:
        raise UnicornException(
            status=400,
            message="Wrong roles"
        )

    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=400,
            message="not existing product"
        )
    
    f = await RoleProduct.get_or_create(role=item.role, product=p)
    if not f[1]:
        raise UnicornException(
            status=400,
            message="existing role"
        )

    return {"error": False, "messsage": ""}


class AddVariantProductItem(BaseModel):
    name: str
    price: float


# admin: add variant to product
@router.post("/{product_id}/variant")
@roles("admin")
async def add_variant_product(
    product_id: int,
    item: AddVariantProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=400,
            message="not existing product"
        )
    
    f = await Variant.get_or_create(
        name=item.name, 
        price=item.price, 
        product=p
    )
    if not f[1]:
        raise UnicornException(
            status=400,
            message="existing variant"
        )

    return {"error": False, "messsage": ""}


class ChangePriceProductItem(BaseModel):
    price: float


# admin: change price product 
@router.put("/{product_id}")
@roles("admin")
async def change_price_product(
    product_id: int,
    item: ChangePriceProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    p = Products.filter(id=product_id)

    if not await p.exists():
        raise UnicornException(
            status=400,
            message="not existing product"
        )
    
    await p.update(price=item.price)

    return {"error": False, "message": ""}


# admin: delete product
@router.delete("/{product_id}")
@roles("admin")
async def delete_product(
    product_id: int,
    token: TokenJwt = Depends(token_jwt)
):
    product = Products.filter(id=product_id)

    if not await product.exists():
        raise UnicornException(
            status=404,
            message="product not exist"
        )
    
    await product.delete()

    return {"error": False, "message": ""}


class DeleteRoleProductItem(BaseModel):
    role: str


# admin: delete role from a product
@router.delete("/{product_id}/role")
@roles("admin")
async def delete_role_product(
    product_id: int,
    item: DeleteRoleProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=404,
            message="product not exist"
        )

    r = RoleProduct.filter(role=item.role, product=p)

    if not await r.exists():
        raise UnicornException(
            status=404,
            message="role not exist"
        )
    
    await r.delete()

    return {"error": False, "message": ""}


class DeleteVariantProductItem(BaseModel):
    name: str


# admin: delete variant from a product
@router.delete("/{product_id}/variant")
@roles("admin")
async def delete_role_product(
    product_id: int,
    item: DeleteVariantProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=404,
            message="product not exist"
        )

    v = Variant.filter(name=item.name, product=p)

    if not await v.exists():
        raise UnicornException(
            status=404,
            message="variant not exist"
        )
    
    await v.delete()

    return {"error": False, "message": ""}
