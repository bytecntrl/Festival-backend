from enum import Enum


class Roles(str, Enum):
    ADMIN = "admin"
    SAGRA = "sagra"
    BAR = "bar"
    PUNTO_GIOVANI = "punto giovani"

    @classmethod
    def is_in_roles(cls, data: str):
        return data in cls.roles()
    
    @classmethod 
    def roles(cls):
        return [x for x in cls._value2member_map_ if x != "admin"] 


class Category(str, Enum):
    FOODS = "foods"
    DRINKS = "drinks"
