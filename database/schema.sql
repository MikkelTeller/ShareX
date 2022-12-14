DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

DROP TABLE IF EXISTS groups;

CREATE TABLE groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    creator INTEGER NOT NULL,
    FOREIGN KEY(creator) REFERENCES users(user_id)
);

DROP TABLE IF EXISTS group_members;

CREATE TABLE group_members (
    group_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    balance INTEGER NOT NULL DEFAULT 0,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(group_id) REFERENCES groups(group_id)
);