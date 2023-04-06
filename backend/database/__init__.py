__all__ = (
    "IngredientOrder", 
    "Ingredients", 
    "Menu", 
    "MenuOrder",
    "MenuProduct", 
    "Orders", 
    "ProductOrder", 
    "Products", 
    "RoleMenu",
    "RoleProduct", 
    "Subcategories", 
    "Users", 
    "Variant"
)


from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from ..config import Session
from .models import (
    IngredientOrder, 
    Ingredients, 
    Menu, 
    MenuOrder,
    MenuProduct, 
    Orders, 
    ProductOrder, 
    Products, 
    RoleMenu,
    RoleProduct, 
    Subcategories, 
    Users, 
    Variant
)


def init_db(app: FastAPI):
    conf = Session.config

    register_tortoise(
        app,
        config={
            "connections": {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": conf.HOST,
                        "port": conf.PORT,
                        "user": conf.DB_USERNAME,
                        "password": conf.PASSWORD,
                        "database": conf.DB_NAME,
                    }
                }
            },
            "apps": {
                "models": {
                    "models": [
                        "backend.database.models",
                    ],
                    "default_connection": "default",
                }
            },
            "timezone": "Europe/Rome"
        },
        generate_schemas=True
    )
