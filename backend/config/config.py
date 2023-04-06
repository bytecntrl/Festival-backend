from asyncio import Lock

from pydantic import BaseSettings


LIST_ENV = [
    "DB_USERNAME",
    "PASSWORD",
    "HOST",
    "PORT",
    "DB_NAME",
    "JWT_SECRET",
    "JWT_TOKEN_EXPIRES",
]


class Config(BaseSettings):
    # db
    DB_USERNAME: str
    PASSWORD: str
    HOST: str
    PORT: str = "5432"
    DB_NAME: str

    # token jwt
    JWT_SECRET: str
    JWT_TOKEN_EXPIRES: int

    # look
    LOCK = Lock()

    # roles
    ROLES: list = [
        "sagra",
        "bar",
        "punto giovani"
    ]
    
    class Config:
        case_sensitive = True

        fields = {
            x: {
                "env": x
            }
            for x in LIST_ENV
        }
