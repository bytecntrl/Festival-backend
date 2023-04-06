from typing import Dict, Union, List, Any
from collections import defaultdict

from schema import Schema, Optional, And, Or
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..config import Session
from ..database import (
    Orders, 
    Products,
    Users,
    Variant,
    Ingredients,
    Menu,
    MenuProduct,
    ProductOrder,
    IngredientOrder,
    MenuOrder,
    RoleProduct,
    RoleMenu,
    Subcategories
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
    "person": Or(And(int, lambda n: n > 0), None),
    "take_away": bool, 
    "table": Or(And(int, lambda n: n > 0), None)
})
SCHEMA_PRODUCT = Schema([
    {
        "id": int, 
        "variant": Or(int, None),
        "ingredient": [int],
        "quantity": int
    }
])
SCHEMA_MENU = Schema([{"id": int, "products": SCHEMA_PRODUCT}])


async def check_product(products, role: str, menu: bool = False) -> bool:
    for x in products:
        product = await Products.filter(id=x["id"]).exists()
        if not product:
            return False

        if (
            not menu and 
            not await RoleProduct.filter(role=role, product_id=x["id"]).exists()
        ):
            return False

        variant = await Variant.filter(
            product_id=x["id"]
        ).values()
        if variant:
            if x.get("variant"):
                if not any(map(lambda y: y["id"] == x["variant"], variant)):
                    return False
            else:
                return False
        if not variant and x.get("variant"):
            return False

        for y in x.get("ingredient", []):
            ingredient = await Ingredients.filter(
                id=y, 
                product_id=x["id"]
            ).exists()
            if not ingredient:
                return False

    return True


async def check_menu(menus, role: str) -> bool:
    for x in menus:
        if not x["products"]:
            return False

        menu = await Menu.filter(id=x["id"]).exists()
        if not menu: 
            return False
        
        if not await RoleMenu.filter(role=role, menu_id=x["id"]).exists():
            return False

        list_product = [
            z["id"] 
            for z in await MenuProduct.filter(menu_id=x["id"]).values() 
            if not z["optional"]
        ]
        ids_product = [y["id"] for y in x["products"]] 

        if not all(map(lambda z: z in ids_product, list_product)):
            return False

        for p in x["products"]:
            product = await MenuProduct.filter(
                menu_id=x["id"],
                product=p["id"]
            ).exists()
            if not product:
                return False

        if not await check_product(x["products"], role, menu=True):
            return False
    
    return True


async def add_products(products, order, menu=None):
    for product in products:
        variant = None
        if product.get("variant"):
            variant = await Variant.get(
                id=product["variant"], 
                product_id=product["id"]
            )
        
        p = await ProductOrder.create(
            menu=menu,
            product=await Products.get(id=product["id"]),
            variant=variant,
            order=order
        )

        for ingredient in product.get("ingredient", []):
            await IngredientOrder(
                ingredient_id=ingredient, 
                product=p, 
                order=order
            ).save()


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    token: TokenJwt = Depends(refresh_token)
):
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise UnicornException(
            status=406,
            message="Order not exist"
        )

    products = await ProductOrder.filter(order=order).values()
    result = defaultdict(list)

    for x in products:
        data = {}
        p = await Products.get(id=x["product_id"])

        data["name"] = p.name
        data["price"] = p.price
        
        variant = await Variant.get_or_none(id=x["variant_id"])
        ingredients = await IngredientOrder.filter(order_id=order_id).values()

        if variant:
            data["variant"] = variant.name

        if ingredients:
            data["ingredients"] = []

        for ingredient in ingredients:
            name = (await Ingredients.get(id=ingredient["ingredient_id"])).name
            data["ingredients"].append(name)
        
        list_order = (await Subcategories.get(id=p.subcategory_id)).order
        result[p.category].insert(list_order, data)

    return {"error": False, "message": "", "product": dict(result)}


class CreateOrdersItem(BaseModel):
    # {"client": str, "person": int, "take_away": bool, "table": int}
    info: Dict[str, Union[str, int, bool, None]]
    # [{"id": int, "variant"?: int, "ingredient"?: [int], "quantity": int}]
    product: List[Dict[str, Union[int, List[int], None]]] = []
    # [{"id": int, "products": product}]
    menu: List[Dict[str, Union[int, Any]]] = []

    class Config:
        smart_union = True


# roles: create orders
@router.post("/")
@roles(Session.config.ROLES)
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
    if not await check_product(item.product, token.role):
        raise UnicornException(
            status=406,
            message="Product not exist"
        )
    if not await check_menu(item.menu, token.role):
        raise UnicornException(
            status=406,
            message="Menu not exist"
        )
    
    info = item.info

    order = await Orders.create(
        client=info["client"],
        person=info.get("person", None),
        take_away=info["take_away"],
        table=info.get("table", None),
        user=await Users.get(username=token.username)
    )

    await add_products(item.product, order)

    for menu in item.menu:
        m = await MenuOrder.create(
            menu_id=menu["id"],
            order=order
        )
        await add_products(menu["products"], order, m)

    return {"error": False, "message": "", "order_id": order.id}
