from flask import Flask, render_template, redirect, session, request
from helpers import get_db_connection, validate_login, validate_registration, add_user, find_groups, find_group, delete_group, find_group_member, add_group_member, get_expenses, get_group_members, dkk, total_balance, user_in_group, user_is_creator, delete_expense, update_balances
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

    # Render homepage
    groups = find_groups(session["user_id"])
    balance = total_balance(session["user_id"]) 
    return render_template("views/index.html", groups=groups, balance=balance)

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

        # If the user didn't fill out the form correctly, an error message will be shown 
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

            # Get the user's data from the database
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()[0]
            conn.close()

            # Log the user in
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            return redirect("/")
        
        # Show error message if registration was filled out incorrectly
        else:
            error_message = validate_registration(username, password, confirm_password)[1]
            return render_template("views/error.html", error_message=error_message), 400

# Logout
@app.route("/logout")
def logout():
    session["user_id"] = None
    session["username"] = None
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

        # Redirect user to Add Member page
        return redirect(f"/add_member?group_id={group_id}")

# Add member page
@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")
    
    group_id = request.args.get("group_id") 

    # If user isn't the creator of the group, the user will be redirected to the home page
    if not user_is_creator(session["user_id"], group_id):
        return redirect("/")

    if request.method == "GET":
        group = find_group(group_id)
        group_members = get_group_members(group_id)
        return render_template("views/add_member.html", group=group, group_members=group_members)

    if request.method == "POST":
        # Check if "Add Member" button is pressed
        if request.form.get("add_member") == "":
            username = request.form.get("username")
            # Check if username is valid and either add the user to the group or show a relevant error message
            if add_group_member(username, group_id)[0]:
                group_members = get_group_members(group_id)
                return redirect(f"/add_member?group_id={group_id}")
            else:
                error_message = add_group_member(username, group_id)[1]
                return render_template("views/error.html", error_message=error_message), 400

        # Check if "Done" button is pressed
        if request.form.get("done") == "":
            return redirect(f"/group?group_id={group_id}")

    

# Group page
@app.route("/group", methods = ["POST", "GET"])
def group():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    group_id = request.args.get("group_id")

    # If user isn't a part of the group, the user will be redirected to the home page
    if not user_in_group(session["user_id"], group_id):
        return redirect("/")

    if request.method == "GET":
        # Get necessary information from database to how the content of the group
        group = find_group(group_id)
        current_group_member = find_group_member(group_id, session["user_id"])[0]
        group_members = get_group_members(group_id)
        expenses = get_expenses(group_id, 5)
        return render_template("views/group.html", group=group, current_group_member=current_group_member, expenses=expenses, group_members=group_members)

    
    if request.method == "POST":
        # Deleting group
        if request.form.get("settle_group") == "":
            return redirect(f"/settle_group?group_id={group_id}")
    
        # Add expense
        if request.form.get("add_expense") == "":
            return redirect(f"/add_expense?group_id={group_id}")
        
        # See all expenses
        if request.form.get("expenses") == "":
            return redirect(f"/expenses?group_id={group_id}")

        # Delete expense
        if request.form.get("delete"):
            expense_id = request.form.get("delete")
            delete_expense(expense_id)
            update_balances(group_id)
            return redirect(f"/group?group_id={group_id}")

# Add expense page
@app.route("/add_expense", methods = ["POST", "GET"])
def add_expense():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    group_id = request.args.get("group_id")
    
    # If user isn't a part of the group, the user will be redirected to the home page
    if not user_in_group(session["user_id"], group_id):
        return redirect("/")

    if request.method == "GET":
        group = find_group(group_id)
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

        # Add the expense to the database. Change the group's "last updated" value
        conn = get_db_connection()
        conn.execute("INSERT INTO expenses(payer, amount, message, time, group_id) VALUES (?, ?, ?, ?, ?)", [payer, amount, message, time, group_id])

        # Change the group's "last updated" value
        conn.execute("UPDATE groups SET last_updated = ? WHERE group_id = ?", [time, group_id])

        conn.commit()
        conn.close()

        # Update the users' balances
        update_balances(group_id)
        return redirect(f"/group?group_id={group_id}")

# Settle Group page
@app.route("/settle_group", methods = ["POST", "GET"])
def settle_group():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    group_id = request.args.get("group_id")

    # If user isn't the creator of the group, the user will be redirected to the home page
    if not user_is_creator(session["user_id"], group_id):
        return redirect("/")

    if request.method == "GET":
        group = find_group(group_id)
        # Get the group members' balances and usernames from the database
        group_members = get_group_members(group_id)
        group_members = sorted(group_members, key=lambda group_member: group_member["balance"], reverse=True)

        # The users with a positive balance are stored in one list and the users with a negative balance are stored in another list
        # They are stored as dicts because the row-objects returned by "get_group_members" don't support item assignment
        positive_group_members = []
        negative_group_members = []

        for group_member in group_members:
            if group_member["balance"] > 0:
                positive_group_members.append({"username": group_member["username"], "balance": group_member["balance"]})
            elif group_member["balance"] < 0:
                negative_group_members.append({"username": group_member["username"], "balance": group_member["balance"]})

        # This list will include descriptions for all the nescessary transfers to settle the group
        transfers = []

        # This block of code generates all the transfer statements
        for positive_group_member in positive_group_members:
            while positive_group_member["balance"] > 0:
                for negative_group_member in negative_group_members:
                    transfer_amount = min(abs(negative_group_member["balance"]), positive_group_member["balance"])
                    negative_group_member["balance"] += transfer_amount
                    positive_group_member["balance"] -= transfer_amount
                    transfers.append({"from": negative_group_member["username"], "to": positive_group_member["username"], "amount": transfer_amount})
        
        return render_template("views/settle_group.html", group=group, transfers=transfers)
    
    if request.method == "POST":
        # Delete Group
        if request.form.get("delete_group") == "":
            # Delete the group and the connected expenses and group members
            delete_group(group_id)
            return redirect("/")
        
        # Cancel settleing the group
        if request.form.get("cancel") == "":
            return redirect(f"/group?group_id={group_id}")

# All expenses page
@app.route("/expenses", methods = ["POST", "GET"])
def expenses():
    # If user isn't logged in, the user will be redirected to the login page
    if session.get("user_id") == None:
        return redirect("/login")

    group_id = request.args.get("group_id")
    
    # If user isn't a part of the group, the user will be redirected to the home page
    if not user_in_group(session["user_id"], group_id):
        return redirect("/")

    if request.method == "GET":
        group = find_group(group_id)
        expenses = get_expenses(group_id)

        return render_template("views/expenses.html", expenses=expenses, group=group)

    if request.method == "POST":
        # Delete expense
        if request.form.get("delete"):
            expense_id = request.form.get("delete")
            delete_expense(expense_id)
            update_balances(group_id)
            return redirect(f"/expenses?group_id={group_id}")

if __name__ == "__main__":
    app.run(debug=True)