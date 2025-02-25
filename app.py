import oracledb  # Oracle Database Library
import os
from flask import Flask, request, jsonify, session, render_template

# 🔹 Flask App Initialization
app = Flask(__name__)
app.secret_key = "f8b7d9e1c2a4567890b3d4e5f6a7c8d9e0f1a2b3c4d5e6f7g8h9i0j1k2l3m4n5"  # Required for session management

# 🔹 Oracle Cloud Database Configuration
USER = "admin"
PASSWORD = "TKM23csa07274671"
DSN = "foodbridge_high"  # Using foodbridge_high from tnsnames.ora

# 🔹 Wallet Configuration
CONFIG_DIR = r"C:\Users\adith\Documents\Wallet_FOODBRIDGE"  # Fix using raw string

WALLET_PASSWORD = "b23csa@TKMCE"  # Wallet password

# 🔹 Set TNS_ADMIN to Wallet Folder
os.environ["TNS_ADMIN"] = CONFIG_DIR

# 🔹 Enable Oracle Thin Mode (No Instant Client Required)
oracledb.defaults.fetch_lobs = False  # Optimizes performance

# 🔹 Function to Connect to Oracle Database
def get_db_connection():
    try:
        connection = oracledb.connect(
            user=USER,
            password=PASSWORD,
            dsn=DSN,
            config_dir=CONFIG_DIR, 
            wallet_location=CONFIG_DIR,  
            wallet_password=WALLET_PASSWORD  
        )
        print("✅ Database connection successful!")
        return connection
    except oracledb.Error as e:
        print("❌ Error connecting to database:", e)
        return None

# 🔹 Route: Serve Home Page
@app.route("/")
def home():
    return render_template("reg.html")

# 🔹 Route: Serve Registration Page
@app.route("/register", methods=["GET"])
def register_page():
    return render_template("reg.html")

# 🔹 Route: Serve Login Page
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("signup.html")

# 🔹 API: Check if Username Exists
@app.route("/check_username", methods=["GET"])
def check_username():
    username = request.args.get("username")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = :username", {"username": username})
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"exists": count > 0})
    return jsonify({"error": "Database connection failed"}), 500

# 🔹 API: Register User
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    role = data.get("role")  # Donor, Volunteer, NGO

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = :username", {"username": username})
            count = cursor.fetchone()[0]
            if count > 0:
                return jsonify({"error": "User already exists"}), 400

            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (:username, :password, :email, :role)",
                {"username": username, "password": password, "email": email, "role": role}
            )
            conn.commit()
            return jsonify({"message": "Registration successful"})
        except oracledb.Error as e:
            return jsonify({"error": str(e)})
        finally:
            cursor.close()
            conn.close()
    return jsonify({"error": "Database connection failed"}), 500

# 🔹 API: User Login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT role FROM users WHERE username = :username AND password = :password",
                {"username": username, "password": password}
            )
            user = cursor.fetchone()
            if user:
                session["user"] = username
                return jsonify({"message": "Login successful", "role": user[0]})
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        except oracledb.Error as e:
            return jsonify({"error": str(e)})
        finally:
            cursor.close()
            conn.close()
    return jsonify({"error": "Database connection failed"}), 500

# 🔹 Run Flask App
if __name__ == "__main__":
    app.run(debug=True)

