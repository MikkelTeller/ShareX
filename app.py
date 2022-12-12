from flask import Flask, render_template, redirect, session, request
from helpers import validate_login

app = Flask(__name__)
app.secret_key = "htg924gt479ghau9w4q7tght4a9uqgthf"

@app.route("/")
def index():
    if session.get("user_id") == None:
        return redirect("/login")
    return render_template("views/index.html")

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
            return render_template("views/error.html", error_message="Username or password was incorrect"), 400

if __name__ == "__main__":
    app.run(debug=True)