import os

from flask import Flask, render_template, request, jsonify, session, url_for
from database import *
from datetime import datetime, timedelta

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    @app.route('/')
    def mainpage():
        return render_template("mainpage.html")
    
    @app.route('/contact')
    def contact():
        return render_template("contact.html")
    
    @app.route('/about')
    def aboutus():
        return render_template("about.html")
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')

        # 🔹 Fetch user from the database
            user = query("SELECT ID, PASSWORD FROM LOGIN WHERE USERNAME = :1", (username,))
        
            if user:  # If user exists
                stored_password = user[0][1]  # Get stored password from DB
                if password == stored_password:  # Check password
                    session['user_id'] = user[0][0]  # Store user ID in session
                    role = query("SELECT ROLE FROM ALLUSERS WHERE ID = :1",(session['user_id'],))
                    user_role = role[0][0]  # Extract role from the query result
                    return jsonify({"success": True, "role": user_role})  # Send redirect URL

            return jsonify({"success": False, "error": "Invalid username or password!"})  # Send error

        return render_template("login.html")
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            print(role)

            existing_user = query("SELECT COUNT(*) FROM LOGIN WHERE USERNAME = :1", (username,))  # ✅ Now works

            if existing_user[0][0] > 0:  
                return jsonify({"success": False, "error": "Username already exists. Choose another."})

            new_id = query("SELECT NVL(MAX(ID), 0) + 1 FROM LOGIN")[0][0]  # Get max ID and increment
            print(new_id)

        #Insert the new user with the generated ID
            insert("INSERT INTO LOGIN (ID, USERNAME, PASSWORD) VALUES (:1, :2, :3)", (new_id, username, password))
        #inserting the role to ALLUSERS table
            insert("INSERT INTO ALLUSERS (ID, ROLE) VALUES (:1, :2)", (new_id, role))
        
            
            
            return jsonify({"success": True})  # Registration successful

        return render_template("register.html")

    
    @app.route('/feedback')
    def feedback():
        return render_template("feedback.html")
    
    @app.route('/support')
    def support():
        return render_template("support.html")
    
    @app.route('/donor', methods=['GET', 'POST'])
    def donor():
        if request.method == "POST":
            try:
                item_name = request.form.get('itemName')
                quantity = int(request.form.get('quantity'))  # Ensure integer
                item_category = request.form.get('itemCategory')
                donation_date = request.form.get('donationDate')
                shelf_life_days = int(request.form.get('shelfLife'))

                # Calculate shelf life (convert to proper date format)
                donation_date_obj = datetime.strptime(donation_date, '%Y-%m-%d')
                shelf_life = (donation_date_obj + timedelta(days=shelf_life_days)).strftime('%Y-%m-%d')

                # Generate new DONATIONID
                x = query("SELECT MAX(DONATIONID) FROM DONATION")
                dono_id = 101 if not x or not x[0][0] else x[0][0] + 1

                # Generate new FOODID
                y = query("SELECT MAX(FOODID) FROM FOOD")
                food_id = 101 if not y or not y[0][0] else y[0][0] + 1

                # Insert into FOOD table (Using parameterized query)
                insert("INSERT INTO FOOD (FOODID, FOODNAME, FOODTYPE, QUANTITY, STATUS, SHELFLIFE) VALUES (:1, :2, :3, :4, :5, TO_DATE(:6, 'YYYY-MM-DD'))", 
                    (food_id, item_name, item_category, quantity, 'ONHOLD', shelf_life))

                return jsonify({"success": True, "message": "Donation successful!"})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)})

        return render_template("donor.html")
    
    @app.route('/donor_profile')
    def donor_profile():
        return render_template("donor_profile.html")
    
    @app.route('/ngo')
    def ngo():
        return render_template("ngo.html")
    
    @app.route('/ngo_profile')
    def ngo_profile():
        return render_template("ngo_profile.html")
    
    @app.route('/volunteer')
    def volunteer():
        return render_template("volunteer.html")
    
    @app.route('/volunteer_profile')
    def volunteer_profile():
        return render_template("volunteer_profile.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)