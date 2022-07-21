from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..database import Ingredients, ProductIngredient, Products
from ..utils import TokenJwt, UnicornException, roles, token_jwt


router = APIRouter(
    prefix="/ingredients",
    tags=["ingredients"]
)


async def check_products(products: List[str]):
    if not products:
        return False
    
    return all([
        await Products.filter(name=x).exists()
        for x in products
    ])


class AddIngredientItem(BaseModel):
    name: str
    price: float
    products: List[str]


# admin: add ingredient
@router.post("/")
@roles("admin")
async def add_ingredient(
    item: AddIngredientItem,
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
    if not await check_products(item.products):
        raise UnicornException(
            status=400,
            message="Wrong products"
        )

    i = await Ingredients.create(name=item.name, price=item.price)

    for x in item.products:
        p = await Products.filter(name=x)
        await ProductIngredient(product=p, ingredient=i).save()

    return {"error": False, "message": ""}


class AddIngredientProductItem(BaseModel):
    product: str


# admin: add product to ingredient
@router.post("/{ingredient_id}")
@roles("admin")
async def add_ingredient_product(
    ingredient_id: int,
    item: AddIngredientProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    i = await Ingredients.get_or_none(id=ingredient_id)
    if not i:
        raise UnicornException(
            status=400,
            message="Wrong ingredient id"
        )
    
    p = await Products.get_or_none(name=item.product)
    if not p:
        raise UnicornException(
            status=400,
            message="Wrong product"
        )

    pi = await ProductIngredient.get_or_create(product=p, ingredient=i)
    if not pi[1]:
        raise UnicornException(
            status=400,
            message="existing product in ingredient"
        )

    return {"error": False, "message": ""}
