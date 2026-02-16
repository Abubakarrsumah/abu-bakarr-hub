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
    ]

    with st.form("charge_form"):
        customer = st.text_input("Customer Name")
        phone = st.selectbox("Device Type", phone_models)
        price = st.slider("Price (Le)", 3, 10, 5)
        card = st.text_input("Card Number (0-100 or blank)")
        submitted = st.form_submit_button("Add")

        if submitted:
            c.execute("""INSERT INTO charging 
                (customer, phone_model, price, card_number, collected, date)
                VALUES (?,?,?,?,?,?)""",
                (customer, phone, price, card, "No", datetime.date.today().isoformat()))
            conn.commit()
            st.success("Added Successfully")

    st.subheader("Search")
    search = st.text_input("Search Card Number")

    query = "SELECT * FROM charging"
    if search:
        query += f" WHERE card_number='{search}'"

    data = pd.read_sql_query(query, conn)

    if not data.empty:
        st.dataframe(data)

        st.write("### Daily Total")
        st.success(f"{data['price'].sum()} Le")

# ================= INVENTORY =================

if menu == "Inventory":
    if st.session_state.role != "admin":
        st.error("Only Admin can manage inventory")
        st.stop()

    st.title("📦 Inventory Control")

    item = st.text_input("Item Name")
    qty = st.number_input("Quantity", 0)
    price = st.number_input("Price")

    if st.button("Add Item"):
        c.execute("INSERT INTO inventory (item,quantity,price) VALUES (?,?,?)",
                  (item, qty, price))
        conn.commit()
        st.success("Item Added")

    inv = pd.read_sql_query("SELECT * FROM inventory", conn)
    st.dataframe(inv)

# ================= STAFF =================

if menu == "Staff":
    if st.session_state.role != "admin":
        st.error("Only Admin can manage staff")
        st.stop()

    st.title("👥 Staff Management")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["staff"])

    if st.button("Add Staff"):
        c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                  (new_user, hash_password(new_pass), role))
        conn.commit()
        st.success("Staff Added")

    staff = pd.read_sql_query("SELECT id,username,role FROM users", conn)
    st.dataframe(staff)

# ================= MAINTENANCE =================

if menu == "Maintenance":
    st.title("⚙ Machine Maintenance")

    mtype = st.selectbox("Type", ["Fuel", "Oil", "Repair"])
    cost = st.number_input("Cost")

    if st.button("Add Record"):
        c.execute("INSERT INTO maintenance (type,cost,date) VALUES (?,?,?)",
                  (mtype, cost, datetime.date.today().isoformat()))
        conn.commit()
        st.success("Saved")

    mdata = pd.read_sql_query("SELECT * FROM maintenance", conn)
    st.dataframe(mdata)

# ================= REPORTS =================

if menu == "Reports":
    st.title("📊 Reports")

    df = pd.read_sql_query("SELECT * FROM charging", conn)
    if not df.empty:
        st.bar_chart(df["price"])
    else:
        st.info("No Data Yet")
