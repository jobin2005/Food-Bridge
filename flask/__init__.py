import os

from flask import Flask, render_template, request, jsonify
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
    def signup():
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')
            x = query(f"SELECT * FROM LOGIN WHERE USERNAME = '{username}'")
            if password == x[0][2]:
                print("Successfully logged in!")
            print(username,password)
        return render_template("login.html")
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == "POST":
            username = request.form.get('username')
            password = request.form.get('password')

            existing_user = query("SELECT COUNT(*) FROM LOGIN WHERE USERNAME = :1", (username,))  # ✅ Now works

            if existing_user[0][0] > 0:  
                return jsonify({"success": False, "error": "Username already exists. Choose another."})

            new_id = query("SELECT NVL(MAX(ID), 0) + 1 FROM LOGIN")[0][0]  # Get max ID and increment

        # 🔹 Step 3: Insert the new user with the generated ID
            insert("INSERT INTO LOGIN (ID, USERNAME, PASSWORD) VALUES (:1, :2, :3)", (new_id, username, password))  # ✅ Now works

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
            item_name = request.form.get('itemName')
            quantity = request.form.get('quantity')
            item_category = request.form.get('itemCategory')
            donation_date = request.form.get('donationDate')
            shelf_life = datetime.date(datetime.strptime(donation_date, '%Y-%m-%d') + timedelta(days=int(request.form.get('shelfLife'))))
            x = query("SELECT DONATIONID FROM DONATION ORDER BY DONATIONID DESC")
            dono_id = 101 if x == [] else x[0]+1
            y = query("SELECT FOODID FROM FOOD ORDER BY FOODID DESC")
            food_id = 101 if y == [] else y[0]+1
            insert(f"INSERT INTO FOOD (FOODID,FOODNAME,FOODTYPE,QUANTITY,STATUS,SHELFLIFE) VALUES ({food_id},'{item_name}','{item_category}',{quantity},'ONHOLD',TO_DATE('{shelf_life}','YYYY-MM-DD'))")
            print(query("SELECT * FROM FOOD"))
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