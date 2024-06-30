from flask import Flask, request, jsonify
from flask_migrate import Migrate
from models import db, Restaurant, RestaurantPizza, Pizza
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

migrate = Migrate(app, db)
db.init_app(app)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.get('/restaurants')
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict(rules=("-restaurant_pizzas",)) for restaurant in restaurants])

@app.get('/restaurants/<int:id>')
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant is None:
        return jsonify({'error': 'Restaurant not found'}), 404
    return jsonify(restaurant.to_dict())

@app.delete('/restaurants/<int:id>')
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant is None:
        return jsonify({'error': 'Restaurant not found'}), 404
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

@app.get('/pizzas')
def get_pizzas():
    try:
        pizzas = Pizza.query.all()
        pizzas_data = [pizza.to_dict(only=("id", "ingredients", "name")) for pizza in pizzas]
        return jsonify(pizzas_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get('/pizzas/<int:id>')
def get_pizza(id):
    pizza = db.session.get(Pizza, id)
    if pizza is None:
        return jsonify({'error': 'Pizza not found'}), 404
    return jsonify(pizza.to_dict())

@app.post('/restaurant_pizzas')
def create_restaurant_pizza():
    data = request.get_json()
    restaurant_id = data.get('restaurant_id')
    pizza_id = data.get('pizza_id')
    price = data.get('price')

    if not restaurant_id or not pizza_id or price is None:
        return jsonify({'error': 'Missing data'}), 400

    if not (1 <= price <= 30):
        return jsonify({'error': 'Price must be between 1 and 30'}), 400

    try:
        restaurant_pizza = RestaurantPizza(restaurant_id=restaurant_id, pizza_id=pizza_id, price=price)
        db.session.add(restaurant_pizza)
        db.session.commit()
        # Fetch restaurant details and include them in the response
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({'error': 'Restaurant not found'}), 404
        return jsonify({
            **restaurant_pizza.to_dict(),
            'restaurant': restaurant.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400



if __name__ == "__main__":
    app.run(port=5555, debug=True)
