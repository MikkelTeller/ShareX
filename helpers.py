import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def get_db_connection():
    connection = sqlite3.connect('database/app.db')
    connection.row_factory = sqlite3.Row
    return connection

# This function checks that the user has typed in a correct username-password combination. If the login is valid, the user_id is also returned
def validate_login(username, password):
    # If the form isn't filled out, the function returns False
    if username == "" or password == "":
        return False, None
    # A connection object to the database.
    conn = get_db_connection()
    # A list of users from the database with the same username as inputted.
    user = conn.execute('SELECT * FROM users WHERE username = ?', [username]).fetchall()
    conn.close()
    # The function returns true if the username doesn't exist in the database
    if len(user) == 0:
        return False, None
    # Check if the hashed password is the same as the hash in the database.
    if not check_password_hash(user[0]["hash"], password):
        return False, None
    # If no erros has been found, the login is valid and the function returns true and the user_id 
    return True, user[0]["user_id"]