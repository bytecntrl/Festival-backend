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


    async def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }


class Ingredients(Model):
    """
    The Ingredients model
    """

    name = fields.CharField(20, unique=True)
    price = fields.FloatField()

    class Meta:
        table = "ingredients"


class Subcategories(Model):
    """
    The Subcategories model
    """

    name = fields.CharField(20)

    class Meta:
        table = "subcategories"


class Products(Model):
    """
    The Products model
    """

    name = fields.CharField(30, unique=True)
    price = fields.FloatField()
    category = fields.CharEnumField(Category)
    subcategory = fields.ForeignKeyField("models.Subcategories")

    class Meta:
        table = "products"


class ProductIngredient(Model):
    """
    The ProductIngredient model
    """

    product = fields.ForeignKeyField("models.Products")
    ingredient = fields.ForeignKeyField("models.Ingredients")

    class Meta:
        table = "product_ingredient"


class RoleProduct(Model):
    """
    The RoleProduct model
    """

    role = fields.CharField(20)
    product = fields.ForeignKeyField("models.Products")

    class Meta:
        table = "role_product"


class Orders(Model):
    """
    The Orders model
    """

    client = fields.CharField(20)
    person = fields.IntField()
    take_away = fields.BooleanField()
    table = fields.IntField(null=True)
    complete = fields.BooleanField(default=False, null=True)
    user = fields.ForeignKeyField("models.Users")

    class Meta:
        table = "orders"


class ProductsOrders(Model):
    """
    The ProductsOrders model
    """

    menu = fields.ForeignKeyField("models.MenuProduct", null=True)
    product = fields.ForeignKeyField("models.Products")
    order = fields.ForeignKeyField("models.Orders")
    ingredient = fields.ForeignKeyField("models.Ingredients", null=True)
    quantity = fields.IntField()

    class Meta:
        table = "products_orders"


class Menu(Model):
    """
    The Menu model
    """

    name = fields.CharField(30, unique=True)

    class Meta:
        table = "menu"


class RoleMenu(Model):
    """
    The RoleMenu model
    """

    role = fields.CharField(20)
    menu = fields.ForeignKeyField("models.Menu")

    class Meta:
        table = "role_menu"


class MenuProduct(Model):
    """
    The MenuProduct model
    """

    menu = fields.ForeignKeyField("models.Menu")
    product = fields.ForeignKeyField("models.Products")
    optional = fields.BooleanField(default=False)

    class Meta:
        table = "menu_product"
