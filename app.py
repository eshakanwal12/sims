import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import config

# Yeh line templates folder ka exact absolute path set karti hai
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

# Secret Key
app.config["SECRET_KEY"] = config.SECRET_KEY


# =========================
# MySQL Connection Function
# =========================


def get_db_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )


# =========================
# Home / Login Page
# =========================


@app.route("/")
def home():
    return render_template("login.html")

# =========================
# Signup Page
# =========================


@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")


# =========================
# Signup
# =========================


@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    fullname = data["fullname"]
    username = data["username"]
    email = data["email"]
    phone = data["phone"]
    password = data["password"]

    # Hash Password
    password = generate_password_hash(password)

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (fullname, username, email, phone, password)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (fullname, username, email, phone, password),
        )

        db.commit()

        return jsonify({"success": True, "message": "Account created successfully."})

    except mysql.connector.IntegrityError:

        db.rollback()

        return (
            jsonify({"success": False, "message": "Username or email already exists."}),
            409,
        )

    except mysql.connector.Error as error:

        db.rollback()

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Login Page
# =========================


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


# =========================
# Login
# =========================


@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data["username"]
    password = data["password"]

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username = %s OR email = %s
            """,
            (username, username),
        )

        user = cursor.fetchone()

        if user:

            if check_password_hash(user["password"], password):

                # Create Session
                session["user_id"] = user["id"]
                session["username"] = user["username"]

                return jsonify({"success": True, "message": "Login successful."})

        return (
            jsonify(
                {"success": False, "message": "Invalid username/email or password."}
            ),
            401,
        )

    except mysql.connector.Error as error:

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Dashboard
# =========================


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("home"))

    full_name = session["username"]

    return render_template("dashboard.html", full_name=full_name)


# =========================
# Logout
# =========================


@app.route("/logout")
def logout():

    # Remove all session data
    session.clear()

    # Redirect to login page
    return redirect(url_for("home"))


# ===============================
# DASHBOARD STATS
# ===============================


@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():

    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(dictionary=True)

        # ===============================
        # TOTAL PRODUCTS
        # ===============================

        cursor.execute("""
            SELECT COUNT(*) AS total_products
            FROM products
            """)

        total_products = cursor.fetchone()["total_products"]

        # ===============================
        # TOTAL CATEGORIES
        # ===============================

        cursor.execute("""
            SELECT COUNT(*) AS total_categories
            FROM categories
            """)

        total_categories = cursor.fetchone()["total_categories"]

        # ===============================
        # TOTAL CUSTOMERS
        # ===============================

        cursor.execute("""
            SELECT COUNT(*) AS total_customers
            FROM customers
            """)

        total_customers = cursor.fetchone()["total_customers"]

        # ===============================
        # LOW STOCK PRODUCTS
        # ===============================

        cursor.execute("""
            SELECT COUNT(*) AS low_stock
            FROM products
            WHERE stock_quantity <= minimum_stock
            """)

        low_stock = cursor.fetchone()["low_stock"]

        # ===============================
        # TODAY'S SALES
        # ===============================

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(final_amount),
                    0
                ) AS today_sales

            FROM sales

            WHERE DATE(created_at) = CURDATE()
            """)

        today_sales = cursor.fetchone()["today_sales"]

        # ===============================
        # RECENT SALES
        # ===============================

        cursor.execute("""
            SELECT
                s.id AS invoice,

                COALESCE(
                    c.customer_name,
                    'Walk-in Customer'
                ) AS customer,

                DATE_FORMAT(
                    s.created_at,
                    '%d %b %Y'
                ) AS date,

                s.final_amount AS amount,

                'Completed' AS status

            FROM sales s

            LEFT JOIN customers c
                ON s.customer_id = c.id

            ORDER BY s.created_at DESC

            LIMIT 5
            """)

        recent_sales = cursor.fetchall()

        # ===============================
        # LOW STOCK PRODUCTS LIST
        # ===============================

        cursor.execute("""
            SELECT
                product_name AS name,
                stock_quantity AS quantity

            FROM products

            WHERE stock_quantity <= minimum_stock

            ORDER BY stock_quantity ASC

            LIMIT 5
            """)

        low_stock_products = cursor.fetchall()

        # ===============================
        # RESPONSE
        # ===============================

        return (
            jsonify(
                {
                    "success": True,
                    "total_products": total_products,
                    "total_categories": total_categories,
                    "total_customers": total_customers,
                    "low_stock": low_stock,
                    "today_sales": float(today_sales or 0),
                    "recent_sales": recent_sales,
                    "low_stock_products": low_stock_products,
                }
            ),
            200,
        )

    except mysql.connector.Error as error:

        print("Dashboard stats database error:", error)

        return (
            jsonify(
                {
                    "success": False,
                    "message": "Database error while loading dashboard stats.",
                }
            ),
            500,
        )

    except Exception as error:

        print("Dashboard stats error:", error)

        return (
            jsonify(
                {
                    "success": False,
                    "message": "Something went wrong while loading dashboard stats.",
                }
            ),
            500,
        )

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# =========================
# Categories Page
# =========================


@app.route("/categories")
def categories():
    return render_template("categories.html")


# =========================
# Get All Categories
# =========================


@app.route("/api/categories", methods=["GET"])
def get_categories():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                id,
                name,
                description,
                status,
                created_at,
                updated_at
            FROM categories
            ORDER BY id DESC
        """)

        categories = cursor.fetchall()

        return jsonify({"success": True, "categories": categories}), 200

    except mysql.connector.Error as error:

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Get One Category
# =========================


@app.route("/api/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                name,
                description,
                status,
                created_at,
                updated_at
            FROM categories
            WHERE id = %s
            """,
            (category_id,),
        )

        category = cursor.fetchone()

        if not category:

            return jsonify({"success": False, "message": "Category not found."}), 404

        return jsonify({"success": True, "category": category}), 200

    except mysql.connector.Error as error:

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Create Category
# =========================


@app.route("/api/categories", methods=["POST"])
def create_category():

    data = request.get_json()

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    status = data.get("status", "active")

    if not name:

        return jsonify({"success": False, "message": "Category name is required."}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        # Check duplicate category
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE LOWER(name) = LOWER(%s)
            """,
            (name,),
        )

        existing_category = cursor.fetchone()

        if existing_category:

            return (
                jsonify({"success": False, "message": "Category already exists."}),
                409,
            )

        cursor.execute(
            """
            INSERT INTO categories
                (name, description, status)
            VALUES
                (%s, %s, %s)
            """,
            (name, description, status),
        )

        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Category created successfully.",
                    "category_id": cursor.lastrowid,
                }
            ),
            201,
        )

    except mysql.connector.Error as error:

        db.rollback()

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Update Category
# =========================


@app.route("/api/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):

    data = request.get_json()

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    status = data.get("status", "active")

    if not name:

        return jsonify({"success": False, "message": "Category name is required."}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        # Check whether category exists
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE id = %s
            """,
            (category_id,),
        )

        category = cursor.fetchone()

        if not category:

            return jsonify({"success": False, "message": "Category not found."}), 404

        # Check duplicate name
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE LOWER(name) = LOWER(%s)
            AND id != %s
            """,
            (name, category_id),
        )

        duplicate = cursor.fetchone()

        if duplicate:

            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Another category with this name already exists.",
                    }
                ),
                409,
            )

        cursor.execute(
            """
            UPDATE categories
            SET
                name = %s,
                description = %s,
                status = %s
            WHERE id = %s
            """,
            (name, description, status, category_id),
        )

        db.commit()

        return (
            jsonify({"success": True, "message": "Category updated successfully."}),
            200,
        )

    except mysql.connector.Error as error:

        db.rollback()

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Delete Category
# =========================


@app.route("/api/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):

    db = get_db_connection()
    cursor = db.cursor()

    try:

        # Check whether category exists
        cursor.execute(
            """
            SELECT id
            FROM categories
            WHERE id = %s
            """,
            (category_id,),
        )

        category = cursor.fetchone()

        if not category:

            return jsonify({"success": False, "message": "Category not found."}), 404

        cursor.execute(
            """
            DELETE FROM categories
            WHERE id = %s
            """,
            (category_id,),
        )

        db.commit()

        return (
            jsonify({"success": True, "message": "Category deleted successfully."}),
            200,
        )

    except mysql.connector.IntegrityError:

        db.rollback()

        return (
            jsonify(
                {
                    "success": False,
                    "message": "Category cannot be deleted because it is being used by a product.",
                }
            ),
            409,
        )

    except mysql.connector.Error as error:

        db.rollback()

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Products Page
# =========================


@app.route("/products")
def products():

    if "user_id" not in session:
        return redirect(url_for("home"))

    full_name = session["username"]

    return render_template("products.html", full_name=full_name)


# =========================
# Get All Products
# =========================


@app.route("/api/products", methods=["GET"])
def get_products():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            products.id,
            products.product_name,
            products.sku,
            products.category_id,
            categories.name AS category_name,
            products.purchase_price,
            products.selling_price,
            products.stock_quantity,
            products.minimum_stock,
            products.description,
            products.created_at,
            products.updated_at
        FROM products
        INNER JOIN categories
            ON products.category_id = categories.id
        ORDER BY products.id DESC
    """

    try:

        cursor.execute(query)

        products = cursor.fetchall()

        return jsonify(products), 200

    except mysql.connector.Error as error:

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Add Product
# =========================


@app.route("/api/products", methods=["POST"])
def add_product():

    data = request.get_json()

    product_name = data.get("product_name")
    sku = data.get("sku")
    category_id = data.get("category_id")
    purchase_price = data.get("purchase_price")
    selling_price = data.get("selling_price")
    stock_quantity = data.get("stock_quantity", 0)
    minimum_stock = data.get("minimum_stock", 5)
    description = data.get("description", "")

    # Validate required fields
    if not product_name or not sku or not category_id:

        return (
            jsonify(
                {
                    "success": False,
                    "message": "Product name, SKU and category are required",
                }
            ),
            400,
        )

    db = get_db_connection()
    cursor = db.cursor()

    query = """
        INSERT INTO products (
            product_name,
            sku,
            category_id,
            purchase_price,
            selling_price,
            stock_quantity,
            minimum_stock,
            description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        product_name,
        sku,
        category_id,
        purchase_price,
        selling_price,
        stock_quantity,
        minimum_stock,
        description,
    )

    try:

        cursor.execute(query, values)

        db.commit()

        product_id = cursor.lastrowid

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Product added successfully",
                    "product_id": product_id,
                }
            ),
            201,
        )

    except mysql.connector.IntegrityError:

        db.rollback()

        return jsonify({"success": False, "message": "SKU already exists"}), 409

    except mysql.connector.Error as error:

        db.rollback()

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()


# =========================
# Get One Product
# =========================


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            products.id,
            products.product_name,
            products.sku,
            products.category_id,
            categories.name AS category_name,
            products.purchase_price,
            products.selling_price,
            products.stock_quantity,
            products.minimum_stock,
            products.description,
            products.created_at,
            products.updated_at
        FROM products
        INNER JOIN categories
            ON products.category_id = categories.id
        WHERE products.id = %s
    """

    try:

        cursor.execute(query, (product_id,))

        product = cursor.fetchone()

        if not product:

            return jsonify({"success": False, "message": "Product not found"}), 404

        return jsonify({"success": True, "product": product}), 200

    except mysql.connector.Error as error:

        return jsonify({"success": False, "message": str(error)}), 500

    finally:

        cursor.close()
        db.close()











if __name__ == "__main__":
    app.run(debug=True)