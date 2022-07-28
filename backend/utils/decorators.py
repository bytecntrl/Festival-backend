from functools import wraps
from typing import Union

from .exception import UnicornException


def roles(role: Union[str, list]):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            token,
            *args, **kwargs
        ):
            if token.role not in role:
                raise UnicornException(
                    status=403,
                    message="not allowed"
                )
            return await func(
                token=token, 
                *args, 
                **kwargs
            )      
        return wrapper
    return decorator
