import secrets
import string

from argon2 import PasswordHasher
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from tortoise.contrib.fastapi import register_tortoise

from backend.config import config, Config
from backend.database import Users
from backend.utils import UnicornException


# env 
load_dotenv()


# config
config.conf = Config()


app = FastAPI()


# plugins
from backend.plugins import auth
from backend.plugins import ingredients
from backend.plugins import menu
from backend.plugins import orders
from backend.plugins import products
from backend.plugins import subcategories
from backend.plugins import users

app.include_router(auth.router)
app.include_router(ingredients.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(products.router)
app.include_router(subcategories.router)
app.include_router(users.router)


# db
register_tortoise(
    app,
    config={
        "connections": {
            "default": {
                "engine": "tortoise.backends.asyncpg",
                "credentials": {
                    "host": config.conf.HOST,
                    "port": config.conf.PORT,
                    "user": config.conf.USERNAME,
                    "password": config.conf.PASSWORD,
                    "database": config.conf.DB_NAME,
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
        }
    },
    generate_schemas=True
)


# error
@app.exception_handler(UnicornException)
async def unicorn_exception_handler(_: Request, exc: UnicornException):
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": True,
            "message": exc.message
        }
    )


# creation admin user if not exist
@app.on_event("startup")
async def startup_event():
    if not await Users.filter(role="admin").exists():
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for _ in range(8))

        ph = PasswordHasher()

        await Users(
            username="admin",
            password=ph.hash(password),
            role="admin"
        ).save()

        print("Username: admin")
        print("Password:", password)
