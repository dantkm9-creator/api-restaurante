import os
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

# Clave de seguridad requerida en el encabezado X-API-KEY
API_KEY = os.environ.get("API_KEY", "mi_clave_secreta_123")


def get_db_connection():
  conn = sqlite3.connect("database.db")
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db_connection()
  conn.execute(
      """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


# Middleware de seguridad: valida que exista la API KEY en los encabezados
@app.before_request
def check_api_key():
  api_key = request.headers.get("X-API-KEY")
  if api_key != API_KEY:
    return (
        jsonify({
            "error": "Acceso no autorizado",
            "message": (
                "Falta el encabezado X-API-KEY o la clave proporcionada es"
                " incorrecta."
            ),
        }),
        401,
    )


# 1. CONSULTAR TODO EL CATÁLOGO (GET)
@app.route("/products", methods=["GET"])
def get_products():
  conn = get_db_connection()
  products = conn.execute("SELECT * FROM products").fetchall()
  conn.close()
  return jsonify([dict(row) for row in products]), 200


# 2. CONSULTAR UN PLATILLO POR ID (GET)
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
  conn = get_db_connection()
  product = conn.execute(
      "SELECT * FROM products WHERE id = ?", (product_id,)
  ).fetchone()
  conn.close()
  if product is None:
    return jsonify({"error": "Platillo no encontrado"}), 404
  return jsonify(dict(product)), 200


# 3. CREAR UN PLATILLO (POST)
@app.route("/products", methods=["POST"])
def create_product():
  data = request.get_json()
  if not data or "name" not in data or "price" not in data or "stock" not in data:
    return (
        jsonify(
            {"error": "Datos incompletos. Se requiere 'name', 'price' y 'stock'"}
        ),
        400,
    )

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
      (data["name"], data["price"], data["stock"]),
  )
  conn.commit()
  new_id = cursor.lastrowid
  conn.close()

  return (
      jsonify({
          "id": new_id,
          "name": data["name"],
          "price": data["price"],
          "stock": data["stock"],
      }),
      201,
  )


# 4. ACTUALIZAR UN PLATILLO (PUT)
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
  data = request.get_json()
  conn = get_db_connection()
  product = conn.execute(
      "SELECT * FROM products WHERE id = ?", (product_id,)
  ).fetchone()

  if product is None:
    conn.close()
    return jsonify({"error": "Platillo no encontrado"}), 404

  name = data.get("name", product["name"])
  price = data.get("price", product["price"])
  stock = data.get("stock", product["stock"])

  conn.execute(
      "UPDATE products SET name = ?, price = ?, stock = ? WHERE id = ?",
      (name, price, stock, product_id),
  )
  conn.commit()
  conn.close()

  return (
      jsonify({"id": product_id, "name": name, "price": price, "stock": stock}),
      200,
  )


# 5. ELIMINAR UN PLATILLO (DELETE)
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
  conn = get_db_connection()
  product = conn.execute(
      "SELECT * FROM products WHERE id = ?", (product_id,)
  ).fetchone()

  if product is None:
    conn.close()
    return jsonify({"error": "Platillo no encontrado"}), 404

  conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
  conn.commit()
  conn.close()

  return (
      jsonify(
          {"message": f"Platillo con ID {product_id} eliminado correctamente"}
      ),
      200,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)