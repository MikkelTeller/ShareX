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

# This function returns all the groups a user is a part of
def find_groups(user_id):
    conn = get_db_connection()

    groups = conn.execute("SELECT * FROM groups JOIN group_members ON group_members.group_id = groups.group_id WHERE user_id = ? ORDER BY last_updated DESC", [user_id]).fetchall()

    conn.close()

    return groups

# Returns group object found with group_id
def find_group(group_id):
    conn = get_db_connection()
    group = conn.execute("SELECT * FROM groups WHERE group_id = ?", [group_id]).fetchall()[0]

    conn.close()

    return group

# Returns group_member object found with group_id and user_id
def find_group_member(group_id, user_id):
    conn = get_db_connection()

    group = conn.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", [group_id, user_id]).fetchall()

    conn.close()

    return group

# Deletes a group and all the connected group members and expenses
def delete_group(group_id):
    conn = get_db_connection()

    conn.execute("DELETE FROM groups WHERE group_id = ?", [group_id])
    conn.execute("DELETE FROM group_members WHERE group_id = ?", [group_id])
    conn.execute("DELETE FROM expenses WHERE group_id = ?", [group_id])

    conn.commit()
    conn.close()

# This function checks if the user can be added to the group
    # If the username is valid: The function returns (True, None) and the user is added to the group
    # If the username is invalid: The function returns (False, error_message) and the user is NOT added to the group
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

# This function returns an ordered list of a given number of expenses in a group. If count isn't specified it returns all the expenses in the group
def get_expenses(group_id, count = False):
    conn = get_db_connection()
    if count:
        expenses = conn.execute("SELECT * FROM group_members LEFT JOIN expenses ON expenses.payer = group_members.group_member_id LEFT JOIN users ON users.user_id = group_members.user_id WHERE expenses.group_id = ? ORDER BY time DESC LIMIT ?", [group_id, count]).fetchall()
    else:
        expenses = conn.execute("SELECT * FROM group_members LEFT JOIN expenses ON expenses.payer = group_members.group_member_id LEFT JOIN users ON users.user_id = group_members.user_id WHERE expenses.group_id = ? ORDER BY time DESC", [group_id]).fetchall()
    conn.close()

    expenses.reverse()
    return expenses

# Returns all group members of the group with the specified group_id
def get_group_members(group_id):
    conn = get_db_connection()

    group_members = conn.execute("SELECT * FROM group_members INNER JOIN users ON users.user_id = group_members.user_id WHERE group_members.group_id = ?", [group_id]).fetchall()

    conn.close()

    return group_members

# Returns formatted amount in DKK
def dkk(number):
    number = str(round(number,2))
    return number + " DKK"

# Returns a user's total balance across all groups. This number is shown in the homepage
def total_balance(user_id):
    conn = get_db_connection()

    balances = conn.execute("SELECT balance FROM group_members INNER JOIN users ON users.user_id = group_members.user_id WHERE users.user_id = ?", [user_id]).fetchall()

    total_balance = 0

    for balance in balances:
        total_balance += balance["balance"]

    conn.close()

    return total_balance

# This function returns True if the user with the specified user_id is in the group with the specified group_id. If not it returns False
def user_in_group(user_id, group_id):
    conn = get_db_connection()

    group_members = conn.execute("SELECT * FROM group_members WHERE group_id = ? AND user_id = ?", [group_id, user_id]).fetchall()

    conn.close()

    if len(group_members) == 0:
        return False
    if len(group_members) == 1:
        return True

# This function returns True if the user with the specified user_id is the creator of the group with the specified group_id. If not it returns False
def user_is_creator(user_id, group_id):
    conn = get_db_connection()

    creators = conn.execute("SELECT * FROM group_members LEFT JOIN groups ON group_members.group_id = groups.group_id WHERE group_members.group_id = ? AND groups.creator = ? AND group_members.user_id = ?", [group_id, user_id, user_id]).fetchall()

    conn.close()

    if len(creators) == 0:
        return False
    if len(creators) == 1:
        return True

# Deletes an expense
def delete_expense(expense_id):
    conn = get_db_connection()

    conn.execute("DELETE FROM expenses WHERE expense_id = ?", [expense_id])

    conn.commit()
    conn.close()

# This function updates all the group members' balances.
def update_balances(group_id):
    group_members = get_group_members(group_id)
    count = len(group_members)
    for group_member in group_members:
        balance = 0
        expenses = get_expenses(group_id)
        for expense in expenses:
            if expense["payer"] == group_member["group_member_id"]:
                balance += float(expense["amount"]) * ((count-1)/count)
            else:
                balance -= float(expense["amount"]) / count
                conn = get_db_connection()
    
        conn = get_db_connection()
        conn.execute("UPDATE group_members SET balance = ? WHERE group_member_id = ?", [balance, group_member["group_member_id"]])

        conn.commit()
        conn.close()