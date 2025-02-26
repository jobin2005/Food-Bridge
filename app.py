from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import oracledb

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Database connection details
dsn = "(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.ap-hyderabad-1.oraclecloud.com))(connect_data=(service_name=gc986a84e81826d_foodbridge_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))"
config = r"C:\Users\katta\OneDrive\Desktop\s4\DBMS\Projrct\Wallet_FOODBRIDGE"
wltloc = r"C:\Users\katta\OneDrive\Desktop\s4\DBMS\Projrct\Wallet_FOODBRIDGE"
wltpass = "b23csa@TKMCE"

def get_db_connection():
    """Establish connection to Oracle DB"""
    return oracledb.connect(user="admin", password="TKM23csa07274671", dsn=dsn, config_dir=config, wallet_location=wltloc, wallet_password=wltpass)

@app.route('/')
def signin_page():
    """Render the sign-in page"""
    return render_template('signin.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission"""
    username = request.json.get('username')
    password = request.json.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check credentials
    cursor.execute("SELECT * FROM allusers WHERE username=:1 AND password=:2", (username, password))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if user:
        session['user'] = username  # Store user session
        return jsonify({'status': 'success', 'message': 'Login successful!', 'redirect': '/dashboard'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid username or password'})

@app.route('/dashboard')
def dashboard():
    """Protected dashboard page"""
    if 'user' in session:
        return f"<h1>Welcome, {session['user']}!</h1><p>You are logged in.</p>"
    else:
        return redirect(url_for('signin_page'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('signin_page'))

if __name__ == '__main__':
    app.run(debug=True)
