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
    refresh_token,
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


# all: get menu
@router.get("/")
async def get_menus(
    token: TokenJwt = Depends(refresh_token)
):
    menu = await Menu.all().values()

    return {"error": False, "message": "", "menu": menu}


# all: get menu from id
@router.get("/{menu_id}")
async def get_menu(
    menu_id: int,
    token: TokenJwt = Depends(refresh_token)
):
    menu = Menu.filter(id=menu_id)

    if not await menu.exists():
        raise UnicornException(
            status=406,
            message="Wrong menu_id"
        )

    menu = (await menu.values())[0]

    if token.role != "admin":
        m = await RoleMenu.get_or_none(role=token.role, menu_id=menu["id"])
        if not m:
            raise UnicornException(
                status=403,
                message="not allowed"
            )
    else:
        menu["roles"] = [
            x["role"] 
            for x in await RoleMenu.filter(menu_id=menu["id"]).values()
        ]
    
    menu["products"] = await MenuProduct.filter(menu_id=menu["id"]).values()

    return {"error": False, "message": "", "menu": menu}


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

    products = remove_equal_dictionaries(item.products)
    
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
    product: str
    optional: bool


# admin: add product
@router.post("/{menu_id}/product")
@roles("admin")
async def add_product(
    menu_id: int,
    item: AddProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    menu = await Menu.get_or_none(id=menu_id)
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


class AddRoleItem(BaseModel):
    role: str


# admin: add role
@router.post("/{menu_id}/role")
@roles("admin")
async def add_role(
    menu_id: int,
    item: AddRoleItem,
    token: TokenJwt = Depends(token_jwt)
):
    if item.role not in config.conf.ROLES:
        raise UnicornException(
            status=406,
            message="Wrong roles"
        )

    menu = await Menu.get_or_none(id=menu_id)

    if not menu:
        raise UnicornException(
            status=406,
            message="Wrong menu"
        )
    
    role = await RoleMenu.get_or_create(role=item.role, menu=menu)

    if not role[1]:
        raise UnicornException(
            status=403,
            message="existing role"
        )

    return {"error": False, "messsage": ""}
