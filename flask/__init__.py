import os

from flask import Flask, render_template, request, jsonify, session, url_for, abort, redirect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import wraps

from database import *
from donor_controller import get_donors_by_pincode
from pincode import get_nearby_pincodes

from donor_controller import get_donors_by_pincode  # You write this
from pincode import get_nearby_pincodes
from flask import abort
from db_utils import get_ngo_pincode

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.role.lower() != role.lower():
                return abort(403, description="Access denied. You're not authorized to view this page.")  # Or redirect to a "not authorized" page
            return f(*args, **kwargs)
        return wrapper
    return decorator

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

        admin_data = query("SELECT ADMIN_ID, NAME, PASSWORD FROM ADMIN_ WHERE ADMIN_ID = :ID", {"ID": user_id})

        if admin_data:
            return User(admin_data[0][0], admin_data[0][1], "admin")
        
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

            admin_data = query("SELECT ADMIN_ID, NAME, PASSWORD FROM ADMIN_ WHERE NAME = :USERNAME", {"USERNAME": username})

            if admin_data:
                if password == admin_data[0][2]:
                    user = User(admin_data[0][0],admin_data[0][1],"admin")
                    login_user(user, remember=True)
                    session['user_id'] = admin_data[0][0]
                    return jsonify({"success": True, "role": "admin"})
                    

            if user_data:  # If user exists
                if password == user_data[0][2]:  # Check password
                    user_role = query("SELECT ROLE FROM ALLUSERS WHERE ID = :1",(user_data[0][0],))[0][0]
                    user = User(user_data[0][0], user_data[0][1], user_role)
                    login_user(user, remember=True)
                    session['user_id'] = user_data[0][0]  # Store user ID in session  
                    return jsonify({"success": True, "role": user_role})  # Search the role from the DB and redirects to the page accordingly
            return jsonify({"success": False, "error": "Invalid username or password!"}) 

        return render_template("login.html", user=current_user)

    
    @app.route('/logout')
    @login_required
    def logout():
        session.clear()  # Clears session data
        logout_user()
        return redirect(url_for('mainpage'))
    
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
            
            role = request.form.get('role')
            if not role:  # If role is still missing, return an error
                return jsonify({"success": False, "error": "Role is missing!"})

            existing_user = query("SELECT COUNT(*) FROM LOGIN WHERE USERNAME = :1", (username,))

            if existing_user[0][0] > 0:  
                return jsonify({"success": False, "error": "Username already exists. Choose another."})
            
            #Creating a new id for a new user
            new_id = query("""
                SELECT MAX(val) FROM (
                    SELECT NVL(MAX(ID), 0) as val FROM LOGIN
                    UNION
                    SELECT NVL(MAX(ID), 0) FROM ALLUSERS
                    UNION
                    SELECT NVL(MAX(ID), 0) FROM DONOR
                    UNION
                    SELECT NVL(MAX(ID), 0) FROM VOLUNTEER
                    UNION
                    SELECT NVL(MAX(ID), 0) FROM NGO
                )
            """)[0][0] + 1 #Incrementing Code

            #Insert new user with ID(TO Table LOGIN)
            insert("INSERT INTO LOGIN (ID, USERNAME, PASSWORD) VALUES (:1, :2, :3)", (new_id, username, password))
            
            #Inserting the roles of the users(TO Table ALLUSERS)
            insert("INSERT INTO ALLUSERS (ID, ROLE) VALUES (:1, :2)", (new_id, role))
        
            #Inserting the personal Details of the user to thier respective Tables
            role = role.lower()

            Fname = request.form.get('first_name')
            Lname = request.form.get('last_name')
            Gender = request.form.get('gender')
            Dob = request.form.get('dob')  # expected input: 'YYYY-MM-DD'
            dob_obj = datetime.strptime(Dob, '%Y-%m-%d')  # parse it
            Dob_formatted = dob_obj.strftime('%d-%m-%Y')  # format to 'DD-MM-YYYY'

            Phone = request.form.get('mobile')
            Email = request.form.get('email')
            
            ngo_name = request.form.get('ngo_name')
            reg_id = request.form.get('reg_id')
            owner_name = request.form.get('owner')   

            # Insert address
            state = request.form.get('state')
            district = request.form.get('district')
            street = request.form.get('street')
            house = request.form.get('house') if role != 'ngo' else None
            pincode = request.form.get('pincode')

            # Check if the address already exists
            if role == 'ngo':
                existing_address = query("SELECT ADDRESSID FROM ADDRESS WHERE STATE = :1 AND DISTRICT = :2 AND STREET = :3 AND PINCODE = :4 AND HOUSE IS NULL", (state, district, street, pincode))
            else:
                existing_address = query("SELECT ADDRESSID FROM ADDRESS WHERE STATE = :1 AND DISTRICT = :2 AND STREET = :3 AND HOUSE = :4 AND PINCODE = :5", (state, district, street, house, pincode))

            if existing_address:
                Add_id = existing_address[0][0]
                if role == "donor":
                    insert("INSERT INTO DONOR (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'DD-MM-YYYY'), :6, :7, :8)", (new_id, Fname, Lname, Gender, Dob_formatted, Phone, Email, Add_id))
                    insert("insert into PHONE (PHONE_NUMBER,USER_ID,ROLE) values (:1,:2,:3)",(Phone,new_id,role))
                    return jsonify({"success": True})
                
                elif role == "volunteer":
                    pincode = request.form.get('pincode')
                    print(new_id)
                    insert("INSERT INTO VOLUNTEER (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID, SERVICEAREA, AVAILABLE) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'DD-MM-YYYY'), :6, :7, :8, :9, :10)", (new_id, Fname, Lname, Gender, Dob_formatted, Phone, Email, Add_id, pincode, 0))
                    insert("insert into PHONE (PHONE_NUMBER,USER_ID,ROLE) values (:1,:2,:3)",(Phone,new_id,role))
                    return jsonify({"success": True})

                elif role == "ngo":
                    insert("INSERT INTO NGO (ID, NGONAME, ADDRESSID, OWNERNAME, EMAIL, PHONE,REGISTRATION_ID) VALUES (:1, :2, :3, :4, :5, :6, :7)", (new_id, ngo_name, Add_id, owner_name, Email, Phone, reg_id))
                    insert("insert into PHONE (PHONE_NUMBER,USER_ID,ROLE) values (:1,:2,:3)",(Phone,new_id,role))
                    return jsonify({"success": True})
                
            else:
                     # Generate new address ID
                Add_id = query("SELECT NVL(MAX(ADDRESSID), 0) + 1 FROM ADDRESS")[0][0]
                
    
            if role == 'ngo':
                insert("INSERT INTO ADDRESS (ADDRESSID, STATE, DISTRICT, STREET, PINCODE) VALUES (:1, :2, :3, :4, :5)",
               (Add_id, state, district, street, pincode))
            else:
                insert("INSERT INTO ADDRESS (ADDRESSID, STATE, DISTRICT, STREET, HOUSE, PINCODE) VALUES (:1, :2, :3, :4, :5, :6)",
               (Add_id, state, district, street, house, pincode))
                
                 # Insert user details
            if role == "donor":
                insert("INSERT INTO DONOR (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'DD-MM-YYYY'), :6, :7, :8)",
                    (new_id, Fname, Lname, Gender, Dob_formatted, Phone, Email, Add_id))
                insert("insert into PHONE (PHONE_NUMBER,USER_ID,ROLE) values (:1,:2,:3)",(Phone,new_id,role))
            elif role == "volunteer":
                pincode = request.form.get('pincode')
                print(new_id)
                insert("INSERT INTO VOLUNTEER (ID, FN, LN, GENDER, DOB, PHONE, EMAIL, ADDRESSID, SERVICEAREA, AVAILABLE) VALUES (:1, :2, :3, :4, TO_DATE(:5, 'DD-MM-YYYY'), :6, :7, :8, :9, :10)",
                    (new_id, Fname, Lname, Gender, Dob_formatted, Phone, Email, Add_id, pincode, 0))
                insert("insert into PHONE (PHONE_NUMBER,USER_ID,ROLE) values (:1,:2,:3)",(Phone,new_id,role))

            elif role == "ngo":
                insert("INSERT INTO NGO (ID, NGONAME, ADDRESSID, OWNERNAME, EMAIL, PHONE,REGISTRATION_ID) VALUES (:1, :2, :3, :4, :5, :6, :7)",
                (new_id, ngo_name, Add_id, owner_name, Email, Phone, reg_id))
                insert("insert into PHONE (PHONE_NUMBER,USER_ID,ROLE) values (:1,:2,:3)",(Phone,new_id,role))
            else:
                return jsonify({"success": False, "error": "Invalid role"}) 
                
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
    @role_required('donor')
    def donor():
        current_date = datetime.now().strftime("%Y-%m-%d")

        user_fn_result = query("SELECT FN FROM DONOR WHERE ID = :ID", {"ID": current_user.id})
        user_fn = user_fn_result[0][0] if user_fn_result else "Donor"

        if request.method == "POST":
            try:
                item_name = request.form.get('itemName')
                quantity = int(request.form.get('quantity'))  # Ensure integer
                item_category = request.form.get('itemCategory')
                donation_date = request.form.get('donationDate')  # Expected format: YYYY-MM-DD
                shelf_life_days = int(request.form.get('shelfLife'))

                # Convert donation date to date object
                donation_date_obj = datetime.strptime(donation_date, '%Y-%m-%d')

                # Format donation date as DD-MM-YYYY
                formatted_donation_date = donation_date_obj.strftime('%d-%m-%Y')

                # Calculate shelf life date and format as DD-MM-YYYY
                shelf_life_date = (donation_date_obj + timedelta(days=shelf_life_days)).strftime('%d-%m-%Y')

                # Generate new DONATIONID
                x = query("SELECT DONATIONID FROM DONATION ORDER BY DONATIONID DESC")
                dono_id = 101 if not x or not x[0][0] else x[0][0] + 1

                # Generate new FOODID
                y = query("SELECT FOODID FROM FOOD ORDER BY FOODID DESC")
                food_id = 101 if not y or not y[0][0] else y[0][0] + 1

                # Insert into FOOD table

                insert("INSERT INTO FOOD (FOODID, FOODNAME, FOODTYPE, QUANTITY, STATUS, SHELFLIFE) VALUES (:1, :2, :3, :4, :5, TO_DATE(:6, 'DD-MM-YYYY'))",
                    (food_id, item_name, item_category, quantity, 'PENDING', shelf_life_date))

                # Insert into DONATION table
                insert("INSERT INTO DONATION (DONATIONID, FOODID, DONORID, STATUS, DONATIONDATE) VALUES (:1, :2, :3, 'PENDING', TO_DATE(:4, 'DD-MM-YYYY'))",
                    (dono_id, food_id, current_user.id, formatted_donation_date))

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
            elif user_role == "ngo":
                profile_data = query("select NGONAME,EMAIL,PHONE,ADDRESSID from NGO where ID = :1", (user_id,))
            else:
                return jsonify({"error": "Invalid user role"}), 400

            if not profile_data or len(profile_data[0]) < 7:
                return jsonify({"error": "Profile data incomplete"}), 404
            
            if user_role == "ngo" and len(profile_data[0]) < 4:
                return jsonify({"error": "NGO profile data incomplete"}), 404
            elif user_role != "ngo" and len(profile_data[0]) < 7:
                return jsonify({"error": "Profile data incomplete"}), 404
            
            if user_role != "ngo":
                address_id = profile_data[0][6]
            else:
                address_id = profile_data[0][3]  # NGO query returns 4 columns; ADDRESSID is the 4th

            if user_role != "ngo":
                address_data = query("SELECT STATE, DISTRICT, STREET, HOUSE, PINCODE FROM ADDRESS WHERE ADDRESSID = :1", (address_id,))
            else:
                address_data = query("SELECT STATE, DISTRICT, STREET,PINCODE FROM ADDRESS WHERE ADDRESSID = :1", (address_id,))
                
            if not address_data:
                return jsonify({"error": "Address not found"}), 404

            username = query("SELECT USERNAME FROM LOGIN WHERE ID = :1", (user_id,))
            if not username:
                return jsonify({"error": "Username not found"}), 404

            if user_role == "ngo":
                user_profile = {
                "username": username[0][0],
                "ngoname": profile_data[0][0],
                "email": profile_data[0][1],
                "phone": profile_data[0][2],
                "state": address_data[0][0],
                "district": address_data[0][1],
                "street": address_data[0][2],
                "pincode": address_data[0][3]
                }
            else:
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
                "pincode": address_data[0][4]
            }

            # Add donor-specific fields
            if user_role == "donor":
                dono_count = query("SELECT COUNT(*) FROM DONATION WHERE DONORID = :1", (user_id,))
                last_dono_result = query("SELECT TO_CHAR(DONATIONDATE, 'FXFMMonth DD, YYYY', 'NLS_DATE_LANGUAGE = American') FROM DONATION WHERE DONATIONID = (SELECT MAX(DONATIONID) FROM DONATION WHERE DONORID = :1)", (user_id,))
                user_profile["total_dono"] = dono_count[0][0] if dono_count else 0
                user_profile["last_dono"] = last_dono_result[0][0] if last_dono_result else "N/A"
            elif user_role == "volunteer":
                delv_count = query("SELECT COUNT(*) FROM DONATION_ASSIGNMENT WHERE VOLUNTEER_ID = :1", (user_id,))
                last_delv_result = query("SELECT TO_CHAR(D.DONATIONDATE, 'FMMonth DD, YYYY', 'NLS_DATE_LANGUAGE = American') FROM DONATION D JOIN DONATION_ASSIGNMENT A ON D.DONATIONID = A.DONATION_ID WHERE A.VOLUNTEER_ID = :1 ORDER BY D.DONATIONDATE DESC FETCH FIRST 1 ROWS ONLY", (user_id,))

                user_profile["total_delv"] = delv_count[0][0] if delv_count else 0
                user_profile["last_delv"] = last_delv_result[0][0] if last_delv_result else "N/A"

            return jsonify(user_profile)

        except Exception as e:
            print("Profile fetch error:", e)
            return jsonify({"error": str(e)}), 500

    @app.route('/update_profile')
    @login_required
    def update_profile():
        return render_template("update_profile.html")

    @app.route('/update_user', methods=['PUT'])
    def update_user():
        try:
            user_id = session.get('user_id')
            user_role = current_user.role
            if not user_id:
                return jsonify({"success": False, "error": "User not logged in"}), 401

           # Handle content type
            data = request.json if request.content_type == 'application/json' else request.form
            
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

 
    @app.route('/accept_donation', methods=['POST'])
    def accept_donation():
        donation_id = request.form.get('donation_id')  # comes from the hidden input in the form
        ngo_id = current_user.id  # gets the current logged-in NGO's user id

        if donation_id and ngo_id:
           update(
            "UPDATE donation SET ngo_id = :ngo_id WHERE donationid = :donation_id",
            {'donation_id': donation_id, 'ngo_id': ngo_id}
        )

        return redirect(url_for('ngo'))
    
    @app.route('/ngo',methods=['GET','POST'])
    @login_required
    @role_required('ngo')
    def ngo():
        user_id = session.get('user_id')
        if not user_id:
            return redirect('/login')

        current_year = datetime.now().year

        # 👉 Total completed donations count
        total_donations = query("SELECT count(*) FROM DONATION_ASSIGNMENT WHERE NGO_ID = :1 and STATUS='COMPLETED'", (user_id,))
        c = total_donations[0][0] if total_donations else 0

        # 👉 NGO name
        name = query("SELECT NGONAME FROM NGO WHERE ID = :1", (user_id,))
        org_name = name[0][0]

        # 👉 Base month dictionary for donation chart
        month_template = {
            'Jan': 0, 'Feb': 0, 'Mar': 0, 'Apr': 0,
            'May': 0, 'Jun': 0, 'Jul': 0, 'Aug': 0,
            'Sep': 0, 'Oct': 0, 'Nov': 0, 'Dec': 0
        }

        # 👉 Monthly donation data for chart (STATUS = 'COMPLETED')
        donation_data = query("""
            SELECT 
                TO_CHAR(DONATIONDATE, 'Mon') AS Month_Name,
                EXTRACT(MONTH FROM DONATIONDATE) AS Month_Number,
                COUNT(*) AS Total_Donations
            FROM 
                DONATION
            WHERE 
                EXTRACT(YEAR FROM DONATIONDATE) = :1
                AND NGO_ID = :2 AND STATUS='COMPLETED' 
            GROUP BY 
                TO_CHAR(DONATIONDATE, 'Mon'),
                EXTRACT(MONTH FROM DONATIONDATE)
            ORDER BY 
                Month_Number
        """, (current_year, user_id))

        # 👉 Fill chart data from the result
        for row in donation_data:
            month_name = row[0].strip()
            c_count = row[2]
            if month_name in month_template:
                month_template[month_name] = c_count

        month_labels = list(month_template.keys())
        donation_values = list(month_template.values())

        # 👉 Unclaimed donation details (STATUS: ACTIVE/PENDING)
        unclaimed_donations = query("""
            SELECT 
                DNR.FN || ' ' || DNR.LN AS Donor_Name,
                ADDR.STREET AS Street_Name,
                D.STATUS AS Donation_Status,
                F.FOODNAME AS Food_Item,
                TO_CHAR(D.DONATIONDATE, 'YYYY-MM-DD') AS Donation_Date
            FROM 
                DONATION D
            JOIN 
                DONOR DNR ON D.DONORID = DNR.ID
            JOIN 
                ADDRESS ADDR ON DNR.ADDRESSID = ADDR.ADDRESSID
            JOIN 
                FOOD F ON D.FOODID = F.FOODID
            WHERE 
                D.NGO_ID = :1
                AND D.STATUS IN ('ACTIVE', 'PENDING')
        """, (user_id,))

        # 👉 Claimed donation details (STATUS: COMPLETED)
        claimed_donations = query("""
            SELECT 
                DNR.FN || ' ' || DNR.LN AS Donor_Name,
                ADDR.STREET AS Street_Name,
                F.FOODNAME AS Food_Item,
                TO_CHAR(D.DONATIONDATE, 'YYYY-MM-DD') AS Donation_Date
            FROM 
                DONATION D
            JOIN 
                DONOR DNR ON D.DONORID = DNR.ID
            JOIN 
                ADDRESS ADDR ON DNR.ADDRESSID = ADDR.ADDRESSID
            JOIN 
                FOOD F ON D.FOODID = F.FOODID
            WHERE 
                D.NGO_ID = :1
                AND D.STATUS='COMPLETED'
        """, (user_id,))

        # 👉 Claimed donation count
        claimed_result = query(
            "SELECT COUNT(*) FROM DONATION_ASSIGNMENT WHERE NGO_ID = :1 AND STATUS = 'COMPLETED'", (user_id,))
        claimed_count = claimed_result[0][0] if claimed_result else 0

        # 👉 Unclaimed donation count
        unclaimed_result = query(
            "SELECT COUNT(*) FROM DONATION WHERE NGO_ID = :1 AND STATUS IN ('ACTIVE', 'PENDING')", (user_id,))
        unclaimed_count = unclaimed_result[0][0] if unclaimed_result else 0

        # ----------------------------------------------
        # Nearby Donors Logic from ngo_donations route
        # ----------------------------------------------
        ngo_pincode = get_ngo_pincode(user_id)

        if not ngo_pincode:
            return "Pincode is required", 400

        nearby_pincodes = get_nearby_pincodes(ngo_pincode, 50)
        all_relevant_pincodes = [ngo_pincode] + nearby_pincodes
        donor_food_data = get_donors_by_pincode(all_relevant_pincodes)
        print("Donor-Food Data:", donor_food_data)

        # 👉 Final render
        return render_template("ngo.html",
            total_donations=c,
            org_name=org_name,
            month_labels=month_labels,
            donation_values=donation_values,
            current_year=current_year,
            unclaimed_donations=unclaimed_donations,
            claimed_donations=claimed_donations,
            claimed_count=claimed_count,
            unclaimed_count=unclaimed_count,
            donor_food_data=donor_food_data
        )

    @app.route('/ngo_profile')
    def ngo_profile():
        return render_template("ngo_profile.html")
    
    @app.route('/assigned_donation')
    @login_required
    def volunteer_dashboard():
        volunteer_id = session.get("user_id")

        records = query("""
            SELECT a.ASSIGNMENT_ID, d.DONATIONID, fi.FOODNAME AS food_item, 
                do.FN || ' ' || do.LN AS donor_name,
                n.NGONAME AS ngo_name,
                a.STATUS
            FROM DONATION d
            JOIN FOOD fi ON d.FOODID = fi.FOODID
            JOIN DONOR do ON d.DONORID = do.ID
            JOIN DONATION_ASSIGNMENT a ON d.DONATIONID = a.DONATION_ID
            JOIN NGO n ON a.NGO_ID = n.ID
            WHERE a.VOLUNTEER_ID = :1
            AND a.STATUS = 'ACTIVE'
        """, (volunteer_id,))

        # Convert result to a list of dicts
        formatted = []
        for r in records:
            formatted.append({
                "assignment_id": r[0],      # Add this
                "donation_id": r[1],
                "food_item": r[2],
                "donor_name": r[3],
                "ngo_name": r[4],
                "status": r[5]              # Add this too for JS
            })

        return jsonify({"records": formatted})


    @app.route('/update_assignment_status', methods=['POST'])
    @login_required
    def update_assignment_status():
        try:
            data = request.get_json()
            new_status = data.get('status')
            
            # Convert assignment_id to integer
            try:
                assignment_id = int(data.get('assignment_id'))
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid assignment ID'}), 400

            if not new_status:
                return jsonify({'success': False, 'error': 'Missing status'}), 400

            # Update the DONATION_ASSIGNMENT table
            update("""
                UPDATE DONATION_ASSIGNMENT
                SET STATUS = :1
                WHERE ASSIGNMENT_ID = :2
            """, (new_status, assignment_id))

            # Update the DONATIONS table
            update("""
                UPDATE DONATION
                SET STATUS = :1
                WHERE DONATIONID = (
                    SELECT DONATION_ID FROM DONATION_ASSIGNMENT WHERE ASSIGNMENT_ID = :2
                )
            """, (new_status, assignment_id))
            
            volunteer_id = session.get("user_id")
            update("""
                UPDATE VOLUNTEER
                SET AVAILABLE = :1
                WHERE ID = :2
            """, (1, volunteer_id))
            

            return jsonify({'success': True})

        except Exception as e:
            print(f"Error updating assignment status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        

    @app.route('/volunteer')
    @login_required
    @role_required('volunteer')
    def volunteer():

        result = query("SELECT FN FROM VOLUNTEER WHERE ID = :ID", {"ID": current_user.id})
        if not result:
            return "Volunteer profile not found", 404  # or redirect, or render a friendly error page
        user_fn = result[0][0]

        return render_template("volunteer.html", user_fn=user_fn)
    
    @app.route('/volunteer_profile')
    def volunteer_profile():
        return render_template("volunteer_profile.html")
    
    @app.route('/admin')
    @login_required
    @role_required('admin')
    def admin():
        unverified_ngos = query("SELECT ID, NGONAME, OWNERNAME, EMAIL, PHONE, REGISTRATION_ID, STATE, DISTRICT, STREET, HOUSE, PINCODE FROM NGO, ADDRESS WHERE VERIFICATION_STATUS = 0 AND NGO.ADDRESSID = ADDRESS.ADDRESSID ORDER BY ID")
        unverified_vols = query("SELECT ID, FN, LN, GENDER, DOB, EMAIL, PHONE, SERVICEAREA, STATE, DISTRICT, STREET, HOUSE, PINCODE FROM VOLUNTEER, ADDRESS WHERE VERIFICATION_STATUS = 0 AND VOLUNTEER.ADDRESSID = ADDRESS.ADDRESSID ORDER BY ID")

        pending_donos = query("SELECT D.DONATIONID, D.FOODID, D.DONORID, D.STATUS, TO_CHAR(D.DONATIONDATE, 'Month DD, YYYY'), D.NGO_ID, R.FN, R.LN, R.PHONE, A.STATE, A.DISTRICT, A.STREET, A.HOUSE, A.PINCODE, F.FOODNAME, F.QUANTITY, TO_CHAR(F.SHELFLIFE, 'DD/MM/YYYY') FROM DONATION D JOIN DONOR R ON D.DONORID = R.ID JOIN ADDRESS A ON R.ADDRESSID = A.ADDRESSID JOIN FOOD F ON D.FOODID = F.FOODID ORDER BY D.DONATIONID")

        avail_vols = query("SELECT * FROM VOLUNTEER WHERE VERIFICATION_STATUS = 1 AND AVAILABLE = 1")

        assigned_vols = query("SELECT * FROM VOLUNTEER, DONATION_ASSIGNMENT WHERE VERIFICATION_STATUS = 1 AND AVAILABLE = 0 AND ID = VOLUNTEER_ID")
        return render_template("admin.html",unverified_ngos=unverified_ngos, pending_donos=pending_donos, unverified_vols=unverified_vols,avail_vols=avail_vols,assigned_vols=assigned_vols)

    @app.route('/verify', methods=['POST'])
    def verify():
        data = request.get_json()
        id = data.get('id')
        role = str(data.get('role')).upper()

        # Validate the role to avoid SQL injection
        if role not in ["NGO", "VOLUNTEER", "DONOR"]:
            return jsonify({"error": "Invalid role"}), 400

        update(f"UPDATE {role} SET VERIFICATION_STATUS = 1 WHERE ID = :1", (id,))

        return jsonify({"message": "User Verified"}), 200
    
    @app.route('/assign', methods=['POST'])
    def assign():
        data = request.get_json()
        vol_id = data.get('vol_id')
        dono_id = data.get('dono_id')

        assign_id = query("SELECT NVL(MAX(ASSIGNMENT_ID), 100) + 1 FROM DONATION_ASSIGNMENT")[0][0]

        update("UPDATE VOLUNTEER SET AVAILABLE = 0 WHERE ID = :1", (vol_id,))
        insert("INSERT INTO DONATION_ASSIGNMENT (ASSIGNMENT_ID, DONATION_ID, VOLUNTEER_ID, NGO_ID, STATUS) VALUES(:1, :2, :3, 29, 'ACTIVE')", (assign_id,dono_id,vol_id))

        return jsonify({"message": "Volunteer Assigned"}), 200
    
    @app.route('/unassign', methods=['POST'])
    def unassign():
        data = request.get_json()
        vol_id = data.get('vol_id')
        dono_id = data.get('dono_id')

        update("UPDATE VOLUNTEER SET AVAILABLE = 1 WHERE ID = :1", (vol_id,))
        delete("DELETE FROM DONATION_ASSIGNMENT WHERE DONATION_ID = :1 AND VOLUNTEER_ID = :2", (dono_id,vol_id))

        return jsonify({"message": "Volunteer Unassigned"}), 200

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)