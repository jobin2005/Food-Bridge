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

            #Fetch user from the database
            user = query("SELECT ID, PASSWORD FROM LOGIN WHERE USERNAME = :1", (username,))
        
            if user:  # If user exists
                stored_password = user[0][1]  
                if password == stored_password:  # Checking password
                    session['user_id'] = user[0][0]  # Store user ID in session(Did this so that this sesion ID can be used to access the user details more quickly)
                    role = query("SELECT ROLE FROM ALLUSERS WHERE ID = :1",(session['user_id'],))
                    user_role = role[0][0]  
                    return jsonify({"success": True, "role": user_role})  # Search the role from the DB and redirects to the pge accordingly

            return jsonify({"success": False, "error": "Invalid username or password!"}) 

        return render_template("login.html")
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            print(role)

            existing_user = query("SELECT COUNT(*) FROM LOGIN WHERE USERNAME = :1", (username,))  

            if existing_user[0][0] > 0:  
                return jsonify({"success": False, "error": "Username already exists. Choose another."})
            
            
            #Creating a new id for a new user
            new_id = query("SELECT NVL(MAX(ID), 0) + 1 FROM LOGIN")[0][0]  #Incrementing Code
            print(new_id)

            #Insert new user with ID(TO Table LOGIN)
            insert("INSERT INTO LOGIN (ID, USERNAME, PASSWORD) VALUES (:1, :2, :3)", (new_id, username, password))
            #Inserting the roles of the users(TO Table ALLUSERS)
            insert("INSERT INTO ALLUSERS (ID, ROLE) VALUES (:1, :2)", (new_id, role))
        
            #Inserting the personal Details of the user to thier respective Tables
            
            #For DONOR(Table is DONATOR)
            Fname = request.form.get('first_name')
            Lname = request.form.get('last_name')
            Gender = request.form.get('gender')
            Dob = request.form.get('dob')
            Phone = request.form.get('mobile')
            Email = request.form.get('email')
            Add_id = 100+new_id
            
            insert("INSERT INTO DONATOR (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'), :6, :7, :8)", (new_id, Fname, Lname, Gender, Dob, Phone, Email, Add_id))
            
            return jsonify({"success": True})  

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
    
    @app.route('/get_profile', methods=['GET'])
    def get_profile():
        try:
            user_id = session.get('user_id')  # Get user ID from session
            print("Session User ID:", session.get('user_id'))

            if not user_id:
                return jsonify({"error": "User not logged in"}), 401

            # Fetch user profile from database
            profile_data = query("SELECT FN, LN, EMAIL, PHONE, GENDER, DOB FROM DONATOR WHERE ID = :1", (user_id,))

            if not profile_data:
                return jsonify({"error": "User not found"}), 404
            
            
            dob_str = profile_data[0][5].strftime('%Y-%m-%d')  # Convert SQL date to string
            dob = datetime.strptime(dob_str, '%Y-%m-%d')  # Convert to datetime object

            # Calculate age
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            # Convert to dictionary
            user_profile = {
                "fname": profile_data[0][0],
                "lname":profile_data[0][1],
                "email": profile_data[0][2],
                "phone": profile_data[0][3],
                "gender": profile_data[0][4],
                "age": age
            }
            
            return jsonify(user_profile)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
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
    @app.route('/logout')
    def logout():
        session.clear()  # ✅ Clears session data
        return jsonify({"success": True, "message": "Logged out successfully"})


    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)