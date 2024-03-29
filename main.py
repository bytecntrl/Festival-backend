import secrets
import string

from argon2 import PasswordHasher
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import Config, Session
from backend.database import Users, init_db
from backend.utils import UnicornException

# env 
load_dotenv()


# config
conf = Session.config = Config()


app = FastAPI()


# CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# plugins
from backend.plugins import auth, menu, orders, products, subcategories, users

app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(orders.router)
app.include_router(products.router)
app.include_router(subcategories.router)
app.include_router(users.router)


# db
init_db(app)


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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    detail = exc.errors()
    message = "Error in:\n"
    message += "\n".join([
        f"{' -> '.join(x['loc'])}:\n    {x['msg']}" 
        for x in detail
    ])

    return JSONResponse(
        status_code=422, 
        content={
            "error": True, 
            "message": message,
            "detail": detail
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
