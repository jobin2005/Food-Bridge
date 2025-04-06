import os

from flask import Flask, render_template, request, jsonify, session, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from database import *
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        user_data = query("SELECT ALLUSERS.ID, USERNAME, ROLE FROM LOGIN, ALLUSERS WHERE LOGIN.ID = ALLUSERS.ID AND LOGIN.ID = :ID", {"ID": user_id})
        if user_data:
            return User(user_data[0][0], user_data[0][1], user_data[0][2])
        return None

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
    
    @app.route("/login", methods=["POST", "GET"])
    def login():
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')

            user_data = query("SELECT ID, USERNAME, PASSWORD FROM LOGIN WHERE USERNAME = :USERNAME", {"USERNAME": username})

            if user_data:  # If user exists
                stored_password = user_data[0][2]  # Get stored password from DB
                if password == stored_password:  # Check password
                    user_role = query("SELECT ROLE FROM ALLUSERS WHERE ID = :1",(user_data[0][0],))
                    user = User(user_data[0][0], user_data[0][1], user_role)
                    login_user(user, remember=True)
                    session['user_id'] = user_data[0][0]  # Store user ID in session  
                    return jsonify({"success": True, "role": user_role})  # Search the role from the DB and redirects to the pge accordingly
            return jsonify({"success": False, "error": "Invalid username or password!"}) 

        return render_template("login.html", user=current_user)

    
    @app.route('/logout')
    @login_required
    def logout():
        session.clear()  # Clears session data
        print(current_user.id)
        logout_user()
        return jsonify({"success": True, "message": "Logged out successfully"})
    
    @app.route('/signup')
    def select_role():
        return render_template("signup.html")
    
    @app.route('/ngo_register')
    def ngo_register():
        return render_template("ngo_register.html")
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        today = date.today()
        min_date = (today - relativedelta(years=18)).isoformat()
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            
            role = request.form.get('role-input')
            if not role:  # If role is still missing, return an error
                return jsonify({"success": False, "error": "Role is missing!"})

            existing_user = query("SELECT COUNT(*) FROM LOGIN WHERE USERNAME = :1", (username,))

            if existing_user[0][0] > 0:  
                return jsonify({"success": False, "error": "Username already exists. Choose another."})
            
            #Creating a new id for a new user
            new_id = query("SELECT NVL(MAX(ID), 0) + 1 FROM LOGIN")[0][0]  #Incrementing Code

            #Insert new user with ID(TO Table LOGIN)
            insert("INSERT INTO LOGIN (ID, USERNAME, PASSWORD) VALUES (:1, :2, :3)", (new_id, username, password))
            
            #Inserting the roles of the users(TO Table ALLUSERS)
            insert("INSERT INTO ALLUSERS (ID, ROLE) VALUES (:1, :2)", (new_id, role))
        
            #Inserting the personal Details of the user to thier respective Tables
            role = role.lower()

            Fname = request.form.get('first_name')
            Lname = request.form.get('last_name')
            Gender = request.form.get('gender')
            Dob = request.form.get('dob')
            Phone = request.form.get('mobile')
            Email = request.form.get('email')

                # Generate Address ID
            result = query("SELECT ADDRESSID FROM ADDRESS ORDER BY ADDRESSID DESC")
            if result:
                Add_id = result[0][0] + 1
            else:
                Add_id = 101  # Starting ID when table is empty

                
            # Insert user details
            if role == "donor":
                insert("INSERT INTO DONOR (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'), :6, :7, :8)",
                    (new_id, Fname, Lname, Gender, Dob, Phone, Email, Add_id))      
            elif role == "volunteer":
                pincode = request.form.get('pincode')
                print(new_id)
                insert("INSERT INTO VOLUNTEER (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID, SERVICEAREA, AVAILABLE) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'YYYY-MM-DD'), :6, :7, :8, :9, :10)",
                    (new_id, Fname, Lname, Gender, Dob, Phone, Email, Add_id, pincode, 0))
            else:
                return jsonify({"success": False, "error": "Invalid role"})

            # Insert address
            state = request.form.get('state')
            district = request.form.get('district')
            street = request.form.get('street')
            house = request.form.get('house')
            pincode = request.form.get('pincode')

            insert("INSERT INTO ADDRESS (ADDRESSID, STATE, DISTRICT, STREET, HOUSE, PINCODE) VALUES (:1, :2, :3, :4, :5, :6)",
                (Add_id, state, district, street, house, pincode))

            return jsonify({"success": True})
          

        return render_template("register.html", min_date=min_date)

    
    @app.route('/feedback')
    def feedback():
        return render_template("feedback.html")
    
    @app.route('/support')
    def support():
        return render_template("support.html")
    
    @app.route('/donor', methods=['GET', 'POST'])
    @login_required
    def donor():
        current_date = datetime.now().strftime("%Y-%m-%d")
        user_fn = query("SELECT FN FROM DONOR WHERE ID = :ID",{"ID":current_user.id})[0][0]
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
                x = query("SELECT DONATIONID FROM DONATION ORDER BY DONATIONID DESC")
                dono_id = 101 if not x or not x[0][0] else x[0][0] + 1

                # Generate new FOODID
                y = query("SELECT FOODID FROM FOOD ORDER BY FOODID DESC")
                food_id = 101 if not y or not y[0][0] else y[0][0] + 1

                # Insert into FOOD table (Using parameterized query)
                insert("INSERT INTO FOOD (FOODID, FOODNAME, FOODTYPE, QUANTITY, STATUS, SHELFLIFE) VALUES (:1, :2, :3, :4, :5, TO_DATE(:6, 'YYYY-MM-DD'))", (food_id, item_name, item_category, quantity, 'ONHOLD', shelf_life))

                insert("INSERT INTO DONATION (DONATIONID, FOODID, DONORID, STATUS, DONATIONDATE) VALUES (:1, :2, :3, 'UNASSIGNED', TO_DATE(:4, 'YYYY-MM-DD'))", (dono_id, food_id, current_user.id, donation_date_obj))

                return jsonify({"success": True, "message": "Donation successful!"})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
 
        return render_template("donor.html", current_date=current_date, user_fn=user_fn)
    
    @app.route('/donor_profile')
    def donor_profile():
        return render_template("donor_profile.html")
    
    @app.route('/get_profile', methods=['GET'])
    @login_required
    def get_profile():
        try:
            user_id = current_user.id
            user_role = current_user.role  # Assuming role is stored in current_user

            if not user_id:
                return jsonify({"error": "User not logged in"}), 401

            if user_role == "donor":
                profile_data = query("SELECT FN, LN, EMAIL, PHONE, GENDER, DOB, ADDRESSID FROM DONOR WHERE ID = :1", (user_id,))
            elif user_role == "volunteer":
                profile_data = query("SELECT FN, LN, EMAIL, PHONE, GENDER, DOB, ADDRESSID FROM VOLUNTEER WHERE ID = :1", (user_id,))
            else:
                return jsonify({"error": "Invalid user role"}), 400

            if not profile_data or len(profile_data[0]) < 7:
                return jsonify({"error": "Profile data incomplete"}), 404

            address_id = profile_data[0][6]
            address_data = query("SELECT STATE, DISTRICT, STREET, HOUSE, PINCODE FROM ADDRESS WHERE ADDRESSID = :1", (address_id,))
            if not address_data:
                return jsonify({"error": "Address not found"}), 404

            username = query("SELECT USERNAME FROM LOGIN WHERE ID = :1", (user_id,))
            if not username:
                return jsonify({"error": "Username not found"}), 404

            dob_str = profile_data[0][5].strftime('%Y-%m-%d') if profile_data[0][5] else "2000-01-01"

            user_profile = {
                "username": username[0][0],
                "fname": profile_data[0][0],
                "lname": profile_data[0][1],
                "email": profile_data[0][2],
                "phone": profile_data[0][3],
                "gender": profile_data[0][4],
                "dob": dob_str,
                "state": address_data[0][0],
                "district": address_data[0][1],
                "street": address_data[0][2],
                "house": address_data[0][3],
                "pincode": address_data[0][4],
                "total_dono": dono_count,
                "last_dono": last_dono
            }

            # Add donor-specific fields
            if user_role == "donor":
                dono_count = query("SELECT COUNT(*) FROM DONATION WHERE DONORID = :1", (user_id,))
                last_dono_result = query(
                    "SELECT TO_CHAR(DONATIONDATE, 'Month DD, YYYY') FROM DONATION WHERE DONATIONID = (SELECT MAX(DONATIONID) FROM DONATION WHERE DONORID = :1)",
                    (user_id,))
                user_profile["total_dono"] = dono_count[0][0] if dono_count else 0
                user_profile["last_dono"] = last_dono_result[0][0] if last_dono_result else "N/A"

            return jsonify(user_profile)

        except Exception as e:
            print("Profile fetch error:", e)
            return jsonify({"error": str(e)}), 500

    @app.route('/update_user', methods=['PUT'])
    def update_user():
        try:
            user_id = session.get('user_id')
            user_role = current_user.role
            if not user_id:
                return jsonify({"success": False, "error": "User not logged in"}), 401

            # Ensure data is received correctly
            if request.content_type == 'application/json':
                data = request.json  # JSON data for PUT
            else:
                data = request.form  # Form data for POST

            new_fname = data.get('first_name')
            new_lname = data.get('last_name')
            new_gender = data.get('gender')
            new_dob = data.get('dob')
            new_phone = data.get('mobile')
            new_email = data.get('email')
            new_username = data.get('username')
            new_state = data.get('state')
            new_district = data.get('district')
            new_street = data.get('street')
            new_house = data.get('house')
            new_pincode = data.get('pincode')
            
            existing_user = query("SELECT COUNT(*) FROM LOGIN WHERE USERNAME = :1 AND ID != :2", (new_username, user_id))
            
            
            if existing_user[0][0] > 0:
                 return jsonify({"success": False, "error": "Username already exists. Choose another."})

            # Extract ADDRESSID properly
            if user_role == "donor":
                add_id_result = query("SELECT ADDRESSID FROM DONOR WHERE ID = :1", (user_id,))
            elif user_role == "volunteer":
                add_id_result = query("SELECT ADDRESSID FROM VOLUNTEER WHERE ID = :1", (user_id,))
            else:
                return jsonify({"success": False, "error": "Invalid user role"}), 400

            if not add_id_result:
                return jsonify({"success": False, "error": "Address ID not found"}), 404

            add_id = add_id_result[0][0]

            # Update all fields
            update("UPDATE LOGIN SET USERNAME = :1 WHERE ID = :2", (new_username, user_id))
            if user_role=="donor":
                update("UPDATE DONOR SET FN = :1, LN = :2, GENDER = :3, DOB = TO_DATE(:4, 'YYYY-MM-DD'), PHONE = :5, EMAIL = :6 WHERE ID = :7",
                (new_fname, new_lname, new_gender, new_dob, new_phone, new_email, user_id))
            elif user_role=="volunteer":
                update("UPDATE VOLUNTEER SET FN = :1, LN = :2, GENDER = :3, DOB = TO_DATE(:4, 'YYYY-MM-DD'), PHONE = :5, EMAIL = :6 WHERE ID = :7",
                (new_fname, new_lname, new_gender, new_dob, new_phone, new_email, user_id))
                
            update("UPDATE ADDRESS SET STATE = :1, DISTRICT = :2, STREET = :3, HOUSE = :4, PINCODE = :5 WHERE ADDRESSID = :6",
                (new_state, new_district, new_street, new_house, new_pincode, add_id))

            return jsonify({"success": True, "message": "User updated successfully"})

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500  # Return error details

    
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

    @app.route('/update_profile')
    def update_profile():
        return render_template("update_profile.html")

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)