from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..config import config
from ..database import (
    Orders, 
    Products, 
    ProductsOrders, 
    Users
)
from ..utils import (
    refresh_token, 
    roles, 
    token_jwt,
    UnicornException
)


router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


class CreateOrdersItem(BaseModel):
    client: str
    person: int
    take_away: bool
    table: int = 0


# roles: create orders
@router.post("/")
@roles(config.conf.ROLES)
async def create_orders(
    item: CreateOrdersItem,
    refresh_token: dict = Depends(refresh_token)
):
    if item.person <= 0:
        raise UnicornException(
            status=400,
            message="Wrong person"
        )

    if item.table <= 0:
        raise UnicornException(
            status=400,
            message="Wrong table"
        )

    user = await Users.get(username=refresh_token["username"])

    p = await Orders.create(
        client=item.client,
        person=item.person,
        take_away=item.take_away,
        table=item.table,
        user=user
    )

    return {
        "error": False,
        "message": "",
        "id": p.id
    }


class AddProductToOrderItem(BaseModel):
    product: str
    quantity: int


# roles: add product to order
@router.put("/{order_id}")
@roles(config.conf.ROLES)
async def add_product_to_order(
    order_id: int,
    item: AddProductToOrderItem,
    refresh_token: dict = Depends(refresh_token)
):
    if item.quantity <= 0:
        raise UnicornException(
            status=400,
            message="Wrong quantity"
        )

    order = await Orders.get_or_none(id=order_id)

    if not order:
        raise UnicornException(
            status=400,
            message="Wrong order_id"
        )
    
    if order.complete:
        raise UnicornException(
            status=400,
            message="Order alredy complete"
        )

    user = await order.user.values()
    if user["username"] != refresh_token["username"]:
        raise UnicornException(
            status=405,
            message="not allowed"
        )
    
    product = await Products.get_or_none(name=item.product)

    if not product:
        raise UnicornException(
            status=400,
            message="Wrong product"
        )

    p = ProductsOrders().filter(product=product, order=order)

    if await p.exists():
        raise UnicornException(
            status=400,
            message="Product alredy exists"
        )

    await ProductsOrders(
        product=product,
        order=order,
        quantity=item.quantity
    ).save()

    return {
        "error": False,
        "message": ""
    }


@router.put("/{order_id}/save")
@roles(config.conf.ROLES)
async def save_order(
    order_id: int,
    token: dict = Depends(token_jwt)
):
    order = await Orders.get_or_none(id=order_id)

    if not order:
        raise UnicornException(
            status=400,
            message="Wrong order_id"
        )

    if order.complete:
        raise UnicornException(
            status=400,
            message="Order already completed"
        )
    
    user = await order.user.values()
    if user["username"] != token["username"]:
        raise UnicornException(
            status=405,
            message="not allowed"
        )

    await Orders.filter(id=order_id).update(complete=True)

    return {
        "error": False,
        "message": ""
    }
