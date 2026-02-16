import streamlit as st
import sqlite3
import hashlib
import datetime
import pandas as pd
import os
import random

st.set_page_config(page_title="abubakarr Enterprise PRO", layout="wide")

# ================= DATABASE =================

def connect_db():
    conn = sqlite3.connect("enterprise.db", check_same_thread=False)
    return conn

conn = connect_db()
c = conn.cursor()

# ================= TABLES =================

c.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS charging(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT,
    phone_model TEXT,
    price REAL,
    card_number TEXT,
    collected TEXT,
    date TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS inventory(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT,
    quantity INTEGER,
    price REAL
)""")

c.execute("""CREATE TABLE IF NOT EXISTS maintenance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    cost REAL,
    date TEXT
)""")

conn.commit()

# ================= SECURITY =================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    return c.fetchone()

# Create default admin if not exists
c.execute("SELECT * FROM users WHERE role='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
              ("admin", hash_password("admin123"), "admin"))
    conn.commit()

# ================= LOGIN =================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 abubakarr Enterprise PRO Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        result = check_login(user, pwd)
        if result:
            st.session_state.logged_in = True
            st.session_state.role = result[3]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

# ================= SIDEBAR =================

st.sidebar.title("abubakarr Enterprise PRO")
menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Charging Registry",
    "Inventory",
    "Staff",
    "Maintenance",
    "Reports"
])

# ================= DASHBOARD =================

if menu == "Dashboard":
    st.title("📊 Business Dashboard")

    today = datetime.date.today().isoformat()

    df = pd.read_sql_query("SELECT * FROM charging WHERE date=?", conn, params=(today,))
    total = df["price"].sum() if not df.empty else 0

    st.metric("💰 Daily Total (Le)", total)

    # Offline AI Prediction (simple average)
    history = pd.read_sql_query("SELECT price FROM charging", conn)
    if not history.empty:
        predicted = history["price"].mean() * 20
        st.info(f"🧠 AI Predicted Income Today: {round(predicted,2)} Le")

# ================= CHARGING REGISTRY =================

if menu == "Charging Registry":
    st.title("🔌 Charging Management")

    phone_models = [
        "Tecno", "Infinix", "Samsung", "iPhone",
        "Itel", "Nokia", "Huawei", "Power Bank",
        "Bluetooth Speaker", "Laptop"
