from flask import Flask, render_template, redirect, session, request
from helpers import get_db_connection, validate_login, validate_registration, add_user, find_groups, find_group, delete_group, find_group_member, add_group_member, get_expenses, get_group_members, dkk
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "htg924gt479ghau9w4q7tght4a9uqgthf"

# Filter to format money
app.jinja_env.filters["dkk"] = dkk

# Homepage
@app.route("/")
def index():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    groups = find_groups(session["user_id"])
    return render_template("views/index.html", groups=groups)

# Login Page
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("views/login.html")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # If the user filled out the form correctly, the user will be logged in and redirected to the homepage.
        if validate_login(username, password)[0]:
            user = validate_login(username, password)[1]

            # Log the user in
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return redirect("/")

        else:
            error_message = validate_login(username, password)[1]
            return render_template("views/error.html", error_message=error_message), 400

# Registration Page
@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("views/register.html")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if validate_registration(username, password, confirm_password)[0]:
            # Add new user to the database
            add_user(username, password)

            # Log the user in
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
            conn.close()

            session["user_id"] = user[0]["user_id"]
            session["username"] = user[0]["username"]

            return redirect("/")
        
        # Error message if registration wasn filled out incorrectly
        else:
            error_message = validate_registration(username, password, confirm_password)[1]
            return render_template("views/error.html", error_message=error_message), 400

# Logout
@app.route("/logout")
def logout():
    session["user_id"] = None
    return redirect("/login")

# Create Group page
@app.route("/create_group", methods = ["GET", "POST"])
def create_group():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    if request.method == "GET":
        return render_template("views/create_group.html")

    if request.method == "POST":
        group_name = request.form.get("group_name")
        time = str(datetime.now())
        print(time)

        # Insert the group in the groups table
        conn = get_db_connection()
        conn.execute("INSERT INTO groups(group_name, last_updated, creator) VALUES (?, ?, ?)", [group_name, time, session["user_id"]])
        conn.commit()
        conn.close()

        # Get the group_id
        conn = get_db_connection()
        group_id = conn.execute("SELECT group_id FROM groups WHERE last_updated = ?", [time]).fetchall()[0]["group_id"]

        # Insert the group member in the group_members table
        conn.execute("INSERT INTO group_members(balance, group_id, user_id) VALUES (0, ?, ?)", [group_id, session["user_id"]])

        conn.commit()
        conn.close()
        return redirect("/")

# Add member page
@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    group_id = request.args.get("group_id")

    if request.method == "GET":
        group = find_group(group_id)[0]
        return render_template("views/add_member.html", group=group)

    if request.method == "POST":
        username = request.form.get("username")
        if add_group_member(username, group_id)[0]:
            return redirect(f"/group?group_id={group_id}")
        else:
            error_message = add_group_member(username, group_id)[1]
            return render_template("views/error.html", error_message=error_message), 400

    

# Group page
@app.route("/group", methods = ["POST", "GET"])
def group():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    # If user isn't a part of the group, the user will be redirected to the home page
    # TODO
    group_id = request.args.get("group_id")

    if request.method == "GET":
        # Get necessary information from database
        group = find_group(group_id)[0]
        current_group_member = find_group_member(group_id, session["user_id"])[0]
        group_members = get_group_members(group_id)
        expenses = get_expenses(group_id)
        return render_template("views/group.html", group=group, current_group_member=current_group_member, expenses=expenses, group_members=group_members)

    
    if request.method == "POST":
        # Deleting group
        if request.form.get("delete") == "":
            delete_group(group_id)
            return redirect("/")
    
       # Add expense
        if request.form.get("add_expense") == "":
            return redirect(f"/add_expense?group_id={group_id}")

       # Add member
        if request.form.get("add_member") == "":
            return redirect(f"/add_member?group_id={group_id}")

# Add expense page
@app.route("/add_expense", methods = ["POST", "GET"])
def add_expense():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    # If user isn't a part of the group, the user will be redirected to the home page
    # TODO

    group_id = request.args.get("group_id")

    if request.method == "GET":
        group = find_group(group_id)[0]
        group_members = get_group_members(group_id)
        return render_template("views/add_expense.html", group_members=group_members, group=group)
    
    if request.method == "POST":
        payer = request.form.get("payer")
        amount = request.form.get("amount")
        message = request.form.get("message")
        time = str(datetime.now())

        # Error checking
        if not amount.isdigit():
            error_message = "Amount must be a number"
            return render_template("views/error.html", error_message=error_message), 400

        if message == "":
            error_message = "Message must be filled out"
            return render_template("views/error.html", error_message=error_message), 400

        if len(message) > 100:
            error_message = "Message too long"
            return render_template("views/error.html", error_message=error_message), 400

        if payer == "Who pays?":
            error_message = "You must choose who pays"
            return render_template("views/error.html", error_message=error_message), 400

        # Add the expense to the database
        conn = get_db_connection()

        conn.execute("INSERT INTO expenses(payer, amount, message, time, group_id) VALUES (?, ?, ?, ?, ?)", [payer, amount, message, time, group_id])

        conn.commit()
        conn.close()

        # Update the users' balances 

        return redirect(f"/group?group_id={group_id}")


if __name__ == "__main__":
    app.run(debug=True)

# TODO:)

# Update users' balances when an expense is added (Calculate from list of expenses)
# Implement "pay my part"
# Show users total balance in home page
# Edit design colors and fonts
# Edit the design of "group members" in the group page
# Add "See all expenses"