import config

import sqlite3
import uuid
import datetime

conn = None

# Table definitions:
# CREATE TABLE users (id text, name text, score integer);
# CREATE TABLE game_history (player1 text, player2 text, settlement integer, timestamp integer);

def create_id():
    # '379cba72-5beb-11e3-b28e-00216a097494', cut before the 0021...
    return str(uuid.uuid1())[:23]

def connect():
    conn = sqlite3.connect(config.db_name)
    return conn

def save_user(user):

    query = "UPDATE "
    if not user.get_id():
        id = create_id()
        user.set_id(id)
        query = "INSERT INTO"

    conn = connect()
    cur = conn.cursor()
    print("%s users (id, name, score) VALUES (?, ?, ?)" % query)

    cur.execute("%s users (id, name, score) VALUES (?, ?, ?)" % query,
        (user.get_id(), user.get_name(), user.get_score()))
    conn.commit()

def load_user(key):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, name, score FROM users WHERE id = ?", (key,))
    res = cur.fetchone()
    if res is None:
        raise Exception("Invalid key")
    return res

def log_game(p1, p2, result):
    if not p1.get_id() and not p2.get_id():
        return # Don't log boring stuff
    conn = connect()
    cur = conn.cursor()
    id1 = p1.get_id()
    if not id1:
        id1 = ""
    id2 = p2.get_id()
    if not id2:
        id2 = ""
    cur.execute("INSERT INTO game_history (player1, player2, settlement, timestamp) VALUES (?, ?, ?, ?)",
            (id1, id2, result, datetime.datetime.now()))

