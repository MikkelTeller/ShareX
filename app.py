from flask import Flask, render_template, redirect, session, request
from helpers import get_db_connection, validate_login, validate_registration, add_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "htg924gt479ghau9w4q7tght4a9uqgthf"

@app.route("/")
def index():
    if session.get("user_id") == None:
        return redirect("/login")
    return render_template("views/index.html", session=session)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("views/login.html")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if validate_login(username, password)[0]:
            session["user_id"] = validate_login(username, password)[1]
            return redirect("/")

        else:
            error_message = validate_login(username, password)[1]
            return render_template("views/error.html", error_message=error_message), 400

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

            # Automatically log the user in
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
            conn.close()

            session["user_id"] = user[0]["user_id"]

            return redirect("/")
        
        else:
            error_message = validate_registration(username, password, confirm_password)[1]
            print("sergo")
            return render_template("views/error.html", error_message=error_message), 400

@app.route("/logout")
def logout():
    session["user_id"] = None
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)