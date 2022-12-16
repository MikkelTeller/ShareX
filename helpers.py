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

    return True, user[0]

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

def find_groups(user_id):
    conn = get_db_connection()

    groups = conn.execute("SELECT * FROM groups JOIN group_members ON group_members.group_id = groups.group_id WHERE user_id = ? ORDER BY last_updated DESC", [user_id]).fetchall()

    conn.close()

    return groups

def find_group(group_id):
    conn = get_db_connection()
    group = conn.execute("SELECT * FROM groups WHERE group_id = ?", [group_id]).fetchall()

    conn.close()

    return group

def find_group_member(group_id, user_id):
    conn = get_db_connection()

    group = conn.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", [group_id, user_id]).fetchall()

    conn.close()

    return group

def delete_group(group_id):
    conn = get_db_connection()

    conn.execute("DELETE FROM groups WHERE group_id = ?", [group_id])

    conn.commit()
    conn.close()

def add_group_member(username, group_id):

    conn = get_db_connection()

    # Check if username exists
    user = conn.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()
    if len(user) != 1:
        error_message = f"User \"{username}\" doesn't exist"
        return False, error_message
    
    # Check if user already is in the group
    user_id = user[0]["user_id"]
    group_member = conn.execute("SELECT * FROM group_members WHERE user_id = ? AND group_id = ?", [user_id, group_id]).fetchall()
    if len(group_member) != 0:
        error_message = f"User \"{username}\" is already in the group"
        return False, error_message

    # Add user to group
    user_id = user[0]["user_id"]
    conn.execute("INSERT INTO group_members(balance, user_id, group_id) VALUES (0, ?, ?)", [user_id, group_id])

    conn.commit()
    conn.close()

    return True, None

def get_expenses(group_id):
    conn = get_db_connection()

    expenses = conn.execute("SELECT * FROM users LEFT JOIN expenses ON expenses.payer = users.user_id WHERE group_id = ? ORDER BY time DESC LIMIT 5", [group_id]).fetchall()

    conn.close()

    return expenses

def get_group_members(group_id):
    conn = get_db_connection()

    group_members = conn.execute("SELECT * FROM group_members INNER JOIN users ON users.user_id = group_members.user_id WHERE group_members.group_id = ?", [group_id]).fetchall()

    conn.close()

    return group_members

def dkk(number):
    number = str(round(number,2))
    return number + " DKK"