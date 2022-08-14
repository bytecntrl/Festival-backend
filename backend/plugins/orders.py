from typing import Dict, Union, List, Any
from webbrowser import get

from schema import Schema, Optional, And
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..config import config
from ..database import (
    Orders, 
    Products,
    Users,
    Variant,
    Ingredients,
    Menu,
    MenuProduct
)
from ..utils import (
    refresh_token, 
    roles, 
    token_jwt,
    UnicornException,
    TokenJwt
)


router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


SCHEMA_INFO = Schema({
    "client": And(str, lambda n: len(n) > 2),
    "person": And(int, lambda n: n > 0),
    "take_away": bool, 
    "table": And(int, lambda n: n > 0)
})
SCHEMA_PRODUCT = Schema([
    {
        "id": int, 
        Optional("variant"): str,
        Optional("ingredient"): [int],
        "quantity": int
    }
])
SCHEMA_MENU = Schema([{"id": int, "products": SCHEMA_PRODUCT}])


async def check_product(products) -> bool:
    result = []

    for x in products:
        product = await Products.filter(id=x["id"]).exists()
        result.append(product)

        variant = await Variant.filter(
            name=x["variant"], 
            product_id=x["id"]
        ).exists()
        result.append(variant)

        for y in x["ingredient"]:
            ingredient = await Ingredients.filter(
                id=y, 
                product_id=x["id"]
            ).exists()
            result.append(ingredient)

    return all(result)


async def check_menu(menus) -> bool:
    result = []

    for x in menus:
        menu = await Menu.filter(id=x["id"]).exists()
        result.append(menu)

        list_product = [
            z["id"] 
            for z in await MenuProduct.filter(menu_id=x["id"]).values() 
            if not z["optional"]
        ]
        if not all(
            z in [y["id"] for y in x["products"]] 
            for z in list_product
        ):
            return False

        for p in x["products"]:
            product = await MenuProduct.filter(
                menu_id=x["id"],
                product=p["id"]
            ).exists()
            result.append(product)

        result.append(await check_product(x["products"]))
    
    return all(result)


class CreateOrdersItem(BaseModel):
    # {"client": str, "person": int, "take_away": bool, "table": int}
    info: Dict[str, Union[str, int, bool]]
    # [{"id": int, "variant": str, "ingredient": [int], "quantity": int}]
    product: List[Dict[str, Union[int, str, List[int]]]] = []
    # [{"id": int, "products": product}]
    menu: List[Dict[str, Union[int, Any]]] = []

    class Config:
        smart_union = True


# roles: create orders
@router.post("/")
@roles(config.conf.ROLES)
async def create_orders(
    item: CreateOrdersItem,
    token: TokenJwt = Depends(token_jwt)
):
    if not item.product and not item.menu:
        raise UnicornException(
            status=406,
            message="No data"
        )
    if not SCHEMA_INFO.is_valid(item.info):
        raise UnicornException(
            status=406,
            message="Wrong info schema"
        )
    if not SCHEMA_PRODUCT.is_valid(item.product):
        raise UnicornException(
            status=406,
            message="Wrong product schema"
        )
    if not SCHEMA_MENU.is_valid(item.menu):
        raise UnicornException(
            status=406,
            message="Wrong menu schema"
        )
    if not await check_product(item.product):
        raise UnicornException(
            status=406,
            message="Product not exist"
        )
    if not await check_menu(item.menu):
        raise UnicornException(
            status=406,
            message="Menu not exist"
        )
    
    info = item.info

    order = await Orders.create(
        client=info["client"],
        person=info["person"],
        take_away=info["take_away"],
        table=info["table"],
        user=await Users.get(username=token.username)
    )

    # TODO: to finish
