import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def get_db_connection():
    connection = sqlite3.connect("database/app.db")
    connection.row_factory = sqlite3.Row
    return connection

# This function checks that the user has typed in a correct username-password combination.
    # If the input is valid: The function returns (True, user_id)
    # If the input is invalid: The function returns (False, error_message)
def validate_login(username, password):

    if username == "" or password == "":
        return False, "Username and Password must be filled out"

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
    conn.close()

    if len(user) == 0:
        return False, "Incorrect username or password"

    if not check_password_hash(user[0]["hash"], password):
        return False, "Incorrect username or password"

    return True, user[0]["user_id"]

# This functions checks if the input is a valid new user.
    # If the input is valid: The function returns (True, None)
    # If the input is invalid: The function returns (False, error_message)
def validate_registration(username, password, confirm_password):
    # Check if username is taken
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
    conn.close()

    if len(user) != 0:
        return False, "Username is taken"

    # Check if password was confirmed correctly
    if not password == confirm_password:
        return False, "Confirm Password must be the same as Password"

    return True, None

# This function adds a new user to the database.
def add_user(username, password):
    conn = get_db_connection()

    hash = generate_password_hash(password)
    conn.execute("INSERT INTO users(username, hash) VALUES (?, ?)", [username, hash])

    conn.commit()
    conn.close()

