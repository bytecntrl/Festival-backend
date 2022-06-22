from functools import wraps
from typing import Union

from .exception import UnicornException


def roles(role: Union[str, list]):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            token=None,
            refresh_token=None,
            *args, **kwargs
        ):
            if token:
                if not token["role"] in role:
                    raise UnicornException(
                        status=405,
                        message="not allowed"
                    )
                return await func(
                    token=token, 
                    *args, 
                    **kwargs
                )
            elif refresh_token:
                if not refresh_token["role"] in role:
                    raise UnicornException(
                        status=405,
                        message="not allowed"
                    )
                return await func(
                    refresh_token=refresh_token, 
                    *args, 
                    **kwargs
                )
            
        return wrapper
    return decorator
