from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy_serializer import SerializerMixin

# Set naming convention for foreign keys
metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)

class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)

    # Relationships
    restaurant_pizzas = relationship('RestaurantPizza', back_populates='restaurant')
    pizzas = relationship('Pizza', secondary='restaurant_pizzas', back_populates='restaurants', overlaps="restaurant_pizzas")

    # Serialization rules
    serialize_rules = ('-restaurant_pizzas.restaurant', '-pizzas.restaurants')

    def to_dict(self, rules=None):
        """Serialize the Restaurant object."""
        if rules:
            return super().to_dict(rules=rules)
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'restaurant_pizzas': [rp.to_dict(rules=rules) for rp in self.restaurant_pizzas],
            'pizzas': [pizza.to_dict(rules=rules) for pizza in self.pizzas]
        }

class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    ingredients = db.Column(db.String, nullable=False)

    # Relationships
    restaurant_pizzas = relationship('RestaurantPizza', back_populates='pizza')
    restaurants = relationship('Restaurant', secondary='restaurant_pizzas', back_populates='pizzas', overlaps="restaurant_pizzas")

    # Serialization rules
    serialize_rules = ('-restaurant_pizzas.pizza', '-restaurants.pizzas')

    def to_dict(self, rules=None):
        """Serialize the Pizza object."""
        if rules:
            return super().to_dict(rules=rules)
        return {
            'id': self.id,
            'name': self.name,
            'ingredients': self.ingredients
        }

class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'), nullable=False)
    price = db.Column(db.Integer, nullable=False)

    # Relationships
    restaurant = relationship("Restaurant", back_populates="restaurant_pizzas", overlaps="pizzas,restaurants")
    pizza = relationship("Pizza", back_populates="restaurant_pizzas", overlaps="pizzas,restaurants")

    # Serialization rules
    serialize_rules = ('-restaurant', '-pizza')

    @db.validates('price')
    def validate_price(self, key, price):
        """Validate the price to be between 1 and 30."""
        if not (1 <= price <= 30):
            raise ValueError("Price must be between 1 and 30")
        return price

    def to_dict(self, rules=None):
        """Serialize the RestaurantPizza object."""
        if rules:
            return super().to_dict(rules=rules)
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'pizza_id': self.pizza_id,
            'price': self.price,
            'pizza': self.pizza.to_dict()  # Include pizza details
        }
