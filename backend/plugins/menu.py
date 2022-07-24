from typing import Dict, List, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from schema import Schema
from tortoise.exceptions import IntegrityError

from ..config import config
from ..database import Menu, MenuProduct, Products, RoleMenu
from ..utils import (
    TokenJwt, 
    UnicornException, 
    remove_equal_dictionaries,
    roles, 
    token_jwt
)


router = APIRouter(
    prefix="/menu",
    tags=["menu"]
)


SCHEMA_MENU = Schema([{"product": str, "optional": bool}])
SCHEMA_ROLE = Schema(config.conf.ROLES)


async def exist_products(products: List[str]) -> bool:
    if not products:
        return False

    return all([
        await Products.filter(name=x["product"]).exists()
        for x in products
    ])


class AddMenuItem(BaseModel):
    name: str
    products: List[Dict[str, Union[str, bool]]]
    roles: List[str]

    class Config:
        smart_union = True


# admin: add menu
@router.post("/")
@roles("admin")
async def add_menu(
    item: AddMenuItem,
    token: TokenJwt = Depends(token_jwt)
):
    products = remove_equal_dictionaries(item.products)

    if not item.name:
        raise UnicornException(
            status=400,
            message="Wrong name"
        )
    if not SCHEMA_MENU.is_valid(item.products):
        raise UnicornException(
            status=400,
            message="Wrong products schema"
        )
    if not SCHEMA_ROLE.is_valid(item.roles):
        raise UnicornException(
            status=400,
            message="Wrong roles schema"
        )
    if not await exist_products(item.products):
        raise UnicornException(
            status=400,
            message="Product not exist"
        )
    
    try:
        menu = await Menu.create(name=item.name)

        for x in list(set(item.roles)):
            await RoleMenu(role=x, menu=menu).save()

        for y in products:
            p = await Products.get(name=y["product"])

            await MenuProduct(
                menu=menu, 
                product=p, 
                optional=y["optional"]
            ).save()
        
        return {"error": False, "message": ""}
    except IntegrityError:
        raise UnicornException(
            status=400,
            message="Menu alredy exists"
        )


class AddProductItem(BaseModel):
    menu_id: int
    product: str
    optional: bool


# admin: add product
@router.put("/product")
@roles("admin")
async def add_product(
    item: AddProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    menu = await Menu.get_or_none(id=item.menu_id)
    if not menu:
        raise UnicornException(
            status=400,
            message="Wrong menu"
        )
    
    p = await Products.get_or_none(name=item.product)
    if not p:
        raise UnicornException(
            status=400,
            message="Wrong product"
        )

    if await MenuProduct.filter(menu=menu, product=p).exists():
        raise UnicornException(
            status=400,
            message="Product already exists"
        )

    await MenuProduct(
        menu=menu, 
        product=p, 
        optional=item.optional
    ).save()

    return {"error": False, "message": ""}
