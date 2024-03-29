from collections import defaultdict
from typing import Dict, List, Union

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from schema import Or, Schema
from tortoise.exceptions import IntegrityError

from ..database import (
    Ingredients, 
    Menu, 
    MenuProduct, 
    Products, 
    RoleProduct,
    Subcategories, 
    Variant
)
from ..utils import (
    TokenJwt, 
    UnicornException, 
    enums,
    remove_equal_dictionaries, 
    roles, 
    token_jwt
)


router = APIRouter(
    prefix="/products",
    tags=["products"]
)


SCHEMA_ROLE = Schema(enums.Roles.roles())
SCHEMA_VARIANT_INGREDIENT = Schema([{"name": str, "price": Or(int, float)}])


# all: get all products
@router.get("/")
async def get_products(
    token: TokenJwt = Depends(token_jwt)
):
    products = defaultdict(list)

    categories = await Subcategories.all().order_by("order").values()

    for category in categories:
        p = await Products.filter(subcategory_id=category["id"]).values()
        for y in p:
            if token.role != "admin":
                r = RoleProduct.filter(role=token.role, product_id=y["id"])
                if not await r.exists():
                    continue
            products[category["name"]].append(y)

    return {
        "error": False,
        "message": "",
        "products": dict(products)
    }


# all: get list of product
@router.get("/list")
async def get_list_product(
    token: TokenJwt = Depends(token_jwt)
):
    return {
        "error": False,
        "message": "",
        "products": [x for x in await Products.all().values("id", "name")]
    }


# all: get a product
@router.get("/{product_id}")
async def get_product(
    product_id: int,
    token: TokenJwt = Depends(token_jwt)
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
                status=403,
                message="not allowed"
            )
    else:
        p["roles"] = [
            x[0] 
            for x in 
            await RoleProduct.filter(product_id=p["id"]).values_list("role")
        ]
    
    p["variant"] = await Variant.filter(product_id=p["id"]).values()
    p["ingredient"] = await Ingredients.filter(product_id=p["id"]).values()

    return {"error": False, "message": "", "product": p}


class AddProductItem(BaseModel):
    name: str
    price: float
    category: enums.Category
    subcategory: int
    roles: List[str] = []
    variant: List[Dict[str, Union[str, float, int]]] = []
    ingredients: List[Dict[str, Union[str, float, int]]] = []

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
            status=406,
            message="Wrong name"
        )
    if item.price <= 0:
        raise UnicornException(
            status=406,
            message="Wrong price"
        )
    if not SCHEMA_ROLE.is_valid(item.roles):
        raise UnicornException(
            status=406,
            message="Wrong roles schema"
        )
    if not SCHEMA_VARIANT_INGREDIENT.is_valid(item.variant):
        raise UnicornException(
            status=406,
            message="Wrong variant schema"
        )
    if not SCHEMA_VARIANT_INGREDIENT.is_valid(item.ingredients):
        raise UnicornException(
            status=406,
            message="Wrong ingredients schema"
        )

    variant = remove_equal_dictionaries(item.variant, "name")
    ingredients = remove_equal_dictionaries(item.ingredients, "name")

    try:
        s = await Subcategories.get_or_none(id=item.subcategory)
        if not s:
            raise UnicornException(
                status=406,
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
            await Variant(name=y["name"], price=float(y["price"]), product=p).save()
        
        for z in ingredients:
            await Ingredients(
                name=z["name"], 
                price=float(z["price"]), 
                product=p
            ).save()

        return {"error": False, "message": ""}

    except IntegrityError:
        raise UnicornException(
            status=406,
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
    if not enums.Roles.is_in_roles(item.role):
        raise UnicornException(
            status=406,
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
    price: Union[int, float]

    class Config:
        smart_union = True


# admin: add variant to product
@router.post("/{product_id}/variant")
@roles("admin")
async def add_variant_product(
    product_id: int,
    item: AddVariantProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    if not item.name:
        raise UnicornException(
            status=406,
            message="Wrong name"
        )
    if item.price < 0:
        raise UnicornException(
            status=406,
            message="Wrong price"
        )
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=400,
            message="not existing product"
        )
    
    f = await Variant.get_or_none(
        name=item.name,
        product=p
    )
    if f:
        raise UnicornException(
            status=400,
            message="existing variant"
        )

    await Variant(name=item.name, price=float(item.price), product=p).save()

    return {"error": False, "messsage": ""}


class AddIngredientProductItem(BaseModel):
    name: str
    price: Union[int, float]

    class Config:
        smart_union = True


# admin: add ingredient to product
@router.post("/{product_id}/ingredient")
@roles("admin")
async def add_variant_product(
    product_id: int,
    item: AddIngredientProductItem,
    token: TokenJwt = Depends(token_jwt)
):
    if not item.name:
        raise UnicornException(
            status=406,
            message="Wrong name"
        )
    if item.price < 0:
        raise UnicornException(
            status=406,
            message="Wrong price"
        )
    p = await Products.get_or_none(id=product_id)

    if not p:
        raise UnicornException(
            status=406,
            message="not existing product"
        )
    
    f = await Ingredients.get_or_none(
        name=item.name, 
        product=p
    )
    if f:
        raise UnicornException(
            status=406,
            message="existing ingredient"
        )

    await Ingredients(name=item.name, price=float(item.price), product=p).save()

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
    if item.price <= 0:
        raise UnicornException(
            status=406,
            message="Wrong price"
        )
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
    product = await Products.get_or_none(id=product_id)

    if not product:
        raise UnicornException(
            status=404,
            message="product not exist"
        )
    
    menu = await MenuProduct.filter(product=product).values()
    ids = [x["menu_id"] for x in menu]
    ids = list(filter(lambda x: ids.count(x)==1, ids))

    for x in ids:
        await Menu.filter(id=x).delete()

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
async def delete_variant_product(
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
async def delete_ingredient_product(
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
