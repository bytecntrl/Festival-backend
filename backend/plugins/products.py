from collections import defaultdict
from operator import itemgetter
from typing import Dict, List, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from schema import Schema
from tortoise.exceptions import IntegrityError

from ..config import config
from ..database import (
    Ingredients, 
    Products, 
    RoleProduct, 
    Subcategories,
    Variant
)
from ..utils import (
    Category, 
    TokenJwt, 
    UnicornException, 
    refresh_token,
    remove_equal_dictionaries, 
    roles, 
    token_jwt
)


router = APIRouter(
    prefix="/products",
    tags=["products"]
)


SCHEMA_ROLE = Schema(config.conf.ROLES)
SCHEMA_VARIANT_INGREDIENT = Schema([{"name": str, "price": float}])


# all: get all products
@router.get("/")
async def get_products(
    token: TokenJwt = Depends(refresh_token)
):
    product = {
        "foods": defaultdict(list),
        "drinks": defaultdict(list)
    }

    category = await Subcategories.all().values()
    category = sorted(category, key=itemgetter("order"))

    for x in category:
        p = await Products.filter(subcategory_id=x["id"]).values()
        for y in p:
            if token.role != "admin":
                r = RoleProduct.filter(role=token.role, product_id=y["id"])
                if not await r.exists():
                    continue
            product[y["category"]][x["name"]].append(y)

    return {
        "error": False,
        "message": "",
        "products": {
            k: dict(v)
            for k, v in product.items()
        }
    }


# all: get list of product
@router.get("/list")
async def get_list_product(
    token: TokenJwt = Depends(refresh_token)
):
    return [x["name"] for x in await Products.all().values()]


# all: get a product
@router.get("/{product_id}")
async def get_product(
    product_id: int,
    token: TokenJwt = Depends(refresh_token)
):
    p = Products.filter(id=product_id)

    if not await p.exists():
        raise UnicornException(
            status=400,
            message="product nonexistent"
        )
    
    p = (await p.values())[0]

    if token.role != "admin":
        r = await RoleProduct.get_or_none(role=token.role, product_id=p["id"])
        if not r:
            raise UnicornException(
                status=401,
                message="not allowed"
            )
    else:
        p["roles"] = await RoleProduct.filter(product_id=p["id"]).values()
    
    p["variant"] = await Variant.filter(product_id=p["id"]).values()
    p["ingredient"] = await Ingredients.filter(product_id=p["id"]).values()

    return {"error": False, "message": "", "product": p}


class AddProductItem(BaseModel):
    name: str
    price: float
    category: Category
    subcategory: str
    roles: List[str]
    variant: List[Dict[str, Union[str, float]]]
    ingredients: List[Dict[str, Union[str, float]]]

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
    if not SCHEMA_VARIANT_INGREDIENT.is_valid(item.variant):
        raise UnicornException(
            status=400,
            message="Wrong variant schema"
        )
    if not SCHEMA_VARIANT_INGREDIENT.is_valid(item.ingredients):
        raise UnicornException(
            status=400,
            message="Wrong ingredients schema"
        )

    variant = remove_equal_dictionaries(item.variant, "name")
    ingredients = remove_equal_dictionaries(item.ingredients, "name")

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

        for x in list(set(item.roles)):
            await RoleProduct(role=x, product=p).save()

        for y in variant:
            await Variant(name=y["name"], price=y["price"], product=p).save()
        
        for z in ingredients:
            await Ingredients(
                name=z["name"], 
                price=z["price"], 
                product=p
            ).save()

        return {"error": False, "message": ""}

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


class AddIngredientProductItem(BaseModel):
    name: str
    price: float


# admin: add ingredient to product
@router.post("/{product_id}/ingredient")
@roles("admin")
async def add_variant_product(
    product_id: int,
    item: AddIngredientProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=400,
            message="not existing product"
        )
    
    f = await Ingredients.get_or_create(
        name=item.name, 
        price=item.price, 
        product=p
    )
    if not f[1]:
        raise UnicornException(
            status=400,
            message="existing ingredient"
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


# admin: delete role from a product
@router.delete("/{product_id}/role/{role}")
@roles("admin")
async def delete_role_product(
    product_id: int,
    role: str,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=404,
            message="product not exist"
        )

    r = RoleProduct.filter(role=role, product=p)

    if not await r.exists():
        raise UnicornException(
            status=404,
            message="role not exist"
        )
    
    await r.delete()

    return {"error": False, "message": ""}


# admin: delete variant from a product
@router.delete("/{product_id}/variant/{name}")
@roles("admin")
async def delete_role_product(
    product_id: int,
    name: str,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=404,
            message="product not exist"
        )

    v = Variant.filter(name=name, product=p)

    if not await v.exists():
        raise UnicornException(
            status=404,
            message="variant not exist"
        )
    
    await v.delete()

    return {"error": False, "message": ""}


# admin: delete ingredient from a product
@router.delete("/{product_id}/ingredient/{name}")
@roles("admin")
async def delete_role_product(
    product_id: int,
    name: str,
    token: TokenJwt = Depends(token_jwt)
):
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=404,
            message="product not exist"
        )

    v = Ingredients.filter(name=name, product=p)

    if not await v.exists():
        raise UnicornException(
            status=404,
            message="ingredient not exist"
        )
    
    await v.delete()

    return {"error": False, "message": ""}
