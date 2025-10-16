import os
from werkzeug.security import generate_password_hash, check_password_hash
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from datetime import datetime, timedelta
from flask import jsonify

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = os.urandom(24)
Session(app)

db = SQL("sqlite:///habit.db")

TYPES = [
        "Hobby",
        "Health and Fitness",
        "Finance",
        "Personal Improvement",
        "Other"
]

EORM = [
    "Times",
    "Minutes"
]

INTERVALS = [
    "Per Day",
    "Per Week",
    "Per Month"
]

TOD = [
    "Morning",
    "Afternoon",
    "Evening",
]


def error(message):
    return render_template("error.html", message=message)

@app.route('/', methods=['GET', 'POST'])
def index():
    """Home page, only for logged-in users"""
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        delete_habit_id = request.form.get("deletehabit")
        if delete_habit_id:
            print("Attempting to delete habit ID:", delete_habit_id)
            try:
                db.execute("DELETE FROM habit_completions WHERE habit_id = ?", delete_habit_id)
                print("Deleted from habit_completions")
                db.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", delete_habit_id, session["user_id"])
                print("Deleted from habits")
                return jsonify({"success": True})
            except Exception as e:
                print("Database error:", e)
                return jsonify({"success": False, "error": str(e)})

        habit_id = request.form.get("habit_id")
        habit_id = int(habit_id)
        completed = request.form.get("completed")

        if habit_id and completed is not None:
            try:
                if completed == "True":
                    print("Received Post:", habit_id, completed)
                    try:
                        db.execute("INSERT INTO habit_completions (habit_id, date, completed) VALUES (?, CURRENT_DATE, ?)", habit_id, True)
                        print("Database connection working")
                    except Exception as e:
                        print("Database connection error:", e)
                elif completed == "False":
                    db.execute("""
                        DELETE FROM habit_completions
                        WHERE habit_id = ? AND date = CURRENT_DATE
                    """, (habit_id))

                return jsonify({"success": True})
            except Exception as e:
                print("Database error:", e)
                return jsonify({"success": False, "error": str(e)})
            
        
       
    habitlines = db.execute("SELECT id, name, type, frequency, eorm, interval FROM habits WHERE user_id = ? GROUP BY name", session["user_id"])

    usernameIndex = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

    return render_template("index.html", username=session.get("username"), habitlines=habitlines, usernameIndex=usernameIndex)


@app.route('/progress', methods=["GET"])
def progress():
    """Show habit progress"""
    if "user_id" not in session:
        return redirect("/login")
    
    habitlines = db.execute("SELECT id, name, type, frequency, eorm, interval FROM habits WHERE user_id = ? GROUP BY name", session["user_id"])

    today = datetime.today()
    date_range = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    def get_original_suffix(day):
        if 10 <= day % 100 <= 20:
            return "th"
        elif day % 10 == 1:
            return "st"
        elif day % 10 == 2:
            return "nd"
        elif day % 10 == 3:
            return "rd"
        else:
            return "th"
        
    combinedDate = [
        (   
            (today + timedelta(days=i)).strftime('%Y-%m-%d'),
            (today + timedelta(days=i)).strftime('%a') + 
            f" {(today + timedelta(days=i)).day}{get_original_suffix((today + timedelta(days=i)).day)}"
        )
        for i in range(7)
    ]

    completions = db.execute("SELECT habit_id, date, completed FROM habit_completions WHERE habit_id IN (SELECT id from habits WHERE user_id = ?) AND date BETWEEN ? AND ?", session["user_id"], date_range[0], date_range[-1])

    completion_status = {
        (row["habit_id"], row["date"]): bool(row["completed"])
        for row in completions
    }

    print("completion status:", completion_status)

    return render_template("progress.html", habitlines=habitlines, combinedDate=combinedDate, completion_status=completion_status)


@app.route('/add', methods=["GET", "POST"])
def add():
    """Add a habit"""
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        habit_name = request.form.get("habit-name")
        habit_type = request.form.get("type")
        frequency = request.form.get("number")
        eorm = request.form.get("eorm")
        interval = request.form.get("interval")
        tod_selected = request.form.getlist("tod")  
        start_date = request.form.get("start-date")
        notes = request.form.get("notes")

        if not habit_name:
            return error("Habit name is required")
        if not habit_type:
            return error("Habit type is required")

        tod_string = ", ".join(tod_selected)

        # Insert data into the database
        db.execute("""
            INSERT INTO habits (user_id, name, type, frequency, eorm, interval, tod, notes, start_date)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            session["user_id"], habit_name, habit_type, frequency, eorm, interval, tod_string, notes, start_date)



        flash("Habit added successfully!", "success")
        return redirect("/")

    return render_template("add.html", types=TYPES, eorm=EORM, intervals=INTERVALS, tod=TOD)



    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":

        # Ensure username and password were submitted
        if not request.form.get("username"):
            return error("Userename is required")
        
        elif not request.form.get("password"):
            return error("Password is required")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and check password
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return error("Invalid username or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        return redirect("/")
    
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""

    if request.method == "POST":

        # Ensure new username and password were submitted
        if not request.form.get("username"):
            return error("Username is required")
        elif not request.form.get("password"):
            return error("Password is required")
        elif not request.form.get("confirmation"):
            return error("Please confirm your password")
        elif request.form.get("password") != request.form.get("confirmation"):
            return error("Passwords don't match")
        
        # Check if username already exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) > 0:
            flash("Username already exists", "danger")
            return error("Username already exists")
        
        # HAsh the password and add it to the database
        hash_pass = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), hash_pass)

        flash("Registered successfully!", "success")
        return redirect("/login")
    
    return render_template("/register.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/login")
    
    usernameProfile = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    
    return render_template("profile.html", usernameProfile=usernameProfile)

@app.route("/change", methods=["GET", "POST"])
def change():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not current_password:
            return error("Current password required")
        if not new_password:
            return error("New password is required")
        if not confirmation:
            return error("Confirmation is required")
        if new_password != confirmation:
            return error("Passwords do not match")
        
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        if len(user) != 1 or not check_password_hash(user[0]["hash"], current_password):
            return error("Invalid current password")
        
        hash_new_pass = generate_password_hash(new_password)
        db.execite("UPDATE users SET hash = ? WHERE id = ?", hash_new_pass, session["user_id"])

        return redirect("/profile")
    
    return render_template("change.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
# flask run --debug