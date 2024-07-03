# app_test.py

from models import db, Restaurant, RestaurantPizza, Pizza
from app import app
from faker import Faker
import pytest

@pytest.fixture(scope="module")
def setup_app():
    """Fixture to set up and tear down the Flask app context."""
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

class TestApp:

    def setup_method(self):
        """Setup method executed before each test method."""
        self.fake = Faker()

    def teardown_method(self):
        """Teardown method executed after each test method."""
        db.session.rollback()

    def test_restaurants(self, setup_app):
        """Retrieves restaurants with GET request to /restaurants"""
        app = setup_app
        with app.app_context():
            # Your test code here
            fake = self.fake
            restaurant1 = Restaurant(name=fake.name(), address=fake.address())
            restaurant2 = Restaurant(name=fake.name(), address=fake.address())
            db.session.add_all([restaurant1, restaurant2])
            db.session.commit()

            restaurants = Restaurant.query.all()

            response = app.test_client().get('/restaurants')
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            response = response.json
            assert [restaurant['id'] for restaurant in response] == [restaurant.id for restaurant in restaurants]
            assert [restaurant['name'] for restaurant in response] == [restaurant.name for restaurant in restaurants]
            assert [restaurant['address'] for restaurant in response] == [restaurant.address for restaurant in restaurants]
            for restaurant in response:
                assert 'restaurant_pizzas' not in restaurant

    def test_restaurants_id(self, setup_app):
        """Retrieves one restaurant using its ID with GET request to /restaurants/<int:id>."""
        app = setup_app
        with app.app_context():
            # Your test code here
            fake = self.fake
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
            db.session.add(restaurant)
            db.session.add(pizza)
            db.session.commit()

            restaurant_pizza = RestaurantPizza(price=10, restaurant_id=restaurant.id, pizza_id=pizza.id)
            db.session.add(restaurant_pizza)
            db.session.commit()

            response = app.test_client().get(f'/restaurants/{restaurant.id}')
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            response = response.json
            assert response['id'] == restaurant.id
            assert response['name'] == restaurant.name
            assert response['address'] == restaurant.address
            assert 'restaurant_pizzas' in response
            assert len(response['restaurant_pizzas']) == 1
            assert response['restaurant_pizzas'][0]['id'] == restaurant_pizza.id
            assert response['restaurant_pizzas'][0]['price'] == restaurant_pizza.price
            assert response['restaurant_pizzas'][0]['pizza']['id'] == pizza.id

    def test_returns_404_if_no_restaurant_to_get(self, setup_app):
        """Returns an error message and 404 status code with GET request to /restaurants/<int:id> by a non-existent ID."""
        app = setup_app
        with app.app_context():
            # Your test code here
            response = app.test_client().get('/restaurants/0')
            assert response.status_code == 404
            assert response.content_type == 'application/json'
            assert response.json.get('error')
            assert response.status_code == 404

    def test_deletes_restaurant_by_id(self, setup_app):
        """Deletes restaurant with DELETE request to /restaurants/<int:id>."""
        app = setup_app
        with app.app_context():
            # Your test code here
            fake = self.fake
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            db.session.add(restaurant)
            db.session.commit()

            response = app.test_client().delete(f'/restaurants/{restaurant.id}')

            assert response.status_code == 204

            result = Restaurant.query.filter(Restaurant.id == restaurant.id).one_or_none()
            assert result is None

    def test_returns_404_if_no_restaurant_to_delete(self, setup_app):
        """Returns an error message and 404 status code with DELETE request to /restaurants/<int:id> by a non-existent ID."""
        app = setup_app
        with app.app_context():
            # Your test code here
            response = app.test_client().get('/restaurants/0')
            assert response.status_code == 404
            assert response.json.get('error') == "Restaurant not found"

    def test_pizzas(self, setup_app):
        """Retrieves pizzas with GET request to /pizzas"""
        app = setup_app
        with app.app_context():
            # Your test code here
            fake = self.fake
            pizza1 = Pizza(name=fake.name(), ingredients=fake.sentence())
            pizza2 = Pizza(name=fake.name(), ingredients=fake.sentence())

            db.session.add_all([pizza1, pizza2])
            db.session.commit()

            response = app.test_client().get('/pizzas')
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            response = response.json

            pizzas = Pizza.query.all()

            assert [pizza['id'] for pizza in response] == [pizza.id for pizza in pizzas]
            assert [pizza['name'] for pizza in response] == [pizza.name for pizza in pizzas]
            assert [pizza['ingredients'] for pizza in response] == [pizza.ingredients for pizza in pizzas]
            for pizza in response:
                assert 'restaurant_pizzas' not in pizza

    def test_creates_restaurant_pizzas(self, setup_app):
        """Creates one restaurant_pizzas using a pizza_id, restaurant_id, and price with a POST request to /restaurant_pizzas."""
        app = setup_app
        with app.app_context():
            # Your test code here
            fake = self.fake
            pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            db.session.add(pizza)
            db.session.add(restaurant)
            db.session.commit()

            # Delete if existing in case price differs
            restaurant_pizza = RestaurantPizza.query.filter_by(
                pizza_id=pizza.id, restaurant_id=restaurant.id).one_or_none()
            if restaurant_pizza:
                db.session.delete(restaurant_pizza)
                db.session.commit()

            response = app.test_client().post(
                '/restaurant_pizzas',
                json={
                    "price": 3,
                    "pizza_id": pizza.id,
                    "restaurant_id": restaurant.id,
                }
            )

            assert response.status_code == 201
            assert response.content_type == 'application/json'
            response = response.json
            assert response['price'] == 3
            assert response['pizza_id'] == pizza.id
            assert response['restaurant_id'] == restaurant.id
            assert response['id']
            assert response['pizza']
            assert response['restaurant']

            query_result = RestaurantPizza.query.filter(
                RestaurantPizza.restaurant_id == restaurant.id, RestaurantPizza.pizza_id == pizza.id).first()
            assert query_result.price == 3

    def test_400_for_validation_error(self, setup_app):
        """Returns a 400 status code and error message if a POST request to /restaurant_pizzas fails."""
        app = setup_app
        with app.app_context():
            # Your test code here
            fake = self.fake
            pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            db.session.add(pizza)
            db.session.add(restaurant)
            db.session.commit()

            # Price not in 1..30
            response = app.test_client().post(
                '/restaurant_pizzas',
                json={
                    "price": 0,
                    "pizza_id": pizza.id,
                    "restaurant_id": restaurant.id,
                }
            )

            assert response.status_code == 400
            assert response.json['errors'] == ["validation errors"]

            response = app.test_client().post(
                '/restaurant_pizzas',
                json={
                    "price": 31,
                    "pizza_id": pizza.id,
                    "restaurant_id": restaurant.id,
                }
            )

            assert response.status_code == 400
            assert response.json['errors'] == ["validation errors"]
