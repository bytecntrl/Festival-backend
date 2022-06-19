from tortoise import fields
from tortoise.models import Model

from ..utils import Category


class Users(Model):
    """
    The User model
    """

    username = fields.CharField(30, unique=True)
    password = fields.TextField()
    role = fields.CharField(20)

    class Meta:
        table = "users"


class Products(Model):
    """
    The Products model
    """

    name = fields.CharField(30, unique=True)
    price = fields.FloatField()
    category = fields.CharEnumField(Category)

    class Meta:
        table = "products"


class Orders(Model):
    """
    The Orders model
    """

    client = fields.CharField(20)
    take_away = fields.BooleanField()
    table = fields.IntField(null=True)

    class Meta:
        table = "orders"


class ProductsOrders(Model):
    """
    The ProductsOrders model
    """

    product = fields.ForeignKeyField("models.Products")
    order = fields.ForeignKeyField("models.Orders")
    quantity = fields.IntField()

    class Meta:
        table = "products_orders"
