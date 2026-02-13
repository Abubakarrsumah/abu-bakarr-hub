import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CORE SETTINGS ---
st.set_page_config(page_title="Abu Bakr Master Hub", layout="wide", initial_sidebar_state="collapsed")

DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "maint": "maintenance_log.csv",
    "missing": "missing_cards.csv",
    "login": "login_creds.csv",
    "sales": "sales_history.csv"
}

# --- 2. SAFE DATA LOADING (FIXES LINE 48 ERROR) ---
def load_safe(key, cols):
    file_path = DB_FILES[key]
    # Check if file exists AND if it has data inside
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except Exception:
            pass # Fall back to creating fresh if reading fails
    
    # Create fresh file if missing or empty to prevent crash
    if key == "login":
        df = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"}])
    elif key == "inv":
        df = pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"])
    else:
        df = pd.DataFrame(columns=cols)
    
    df.to_csv(file_path, index=False)
    return df

# Initialize databases using the safe loader
login_df = load_safe("login", ["role", "user", "pw"])
cust_df = load_safe("cust", ["Date", "Card", "Name", "Item", "Price", "Status"])
inv_df = load_safe("inv", ["Item", "Stock", "Price", "Cost"])
maint_df = load_safe("maint", ["Date", "Action", "Cost"])

# --- 3. SECURITY ENGINE ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("🛡️ Master Controller Login")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Access System"):
        match = login_df[(login_df['user'].str.lower() == u) & (login_df['pw'].astype(str) == p)]
        if not match.empty:
            st.session_state.auth = match.iloc[0]['role']
            st.session_state.user = u
            st.rerun()
        else: st.error("Access Denied: Check details")
    st.stop()

# --- 4. SIDEBAR (3-BAG SYSTEM) ---
st.sidebar.title(f"🚀 {st.session_state.auth.upper()} PORTAL")
total_revenue = cust_df['Price'].sum() if not cust_df.empty else 0
st.sidebar.write(f"**Total Rev:** Le {total_revenue}")
st.sidebar.warning(f"Bag 1 (Ops): Le 124.0")
bag2 = st.sidebar.number_input("Bag 2 (Restock)", 0.0)
st.sidebar.success(f"Bag 3 (Wealth): Le {total_revenue - 124.0 - bag2 - 30}")

menu = ["🔌 Charging Registry", "🛒 Retail & POS", "🔧 Maintenance", "⚙️ Master Control"]
choice = st.sidebar.radio("Navigation", menu)

# --- 5. CHARGING REGISTRY (FIXED INDENTATION) ---
if choice == "🔌 Charging Registry":
    st.header("⚡ Charging Management")
    with st.form("entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        card = c1.selectbox("Card Number", list(range(0, 101)))
        name = c2.text_input("Customer Name")
        item_type = c1.selectbox("Device Type", ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Power Bank", "Other"])
        fee = c2.select_slider("Price (Le)", options=list(range(3, 11)))
        if st.form_submit_button("Register Device"):
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Card": card, "Name": name, "Item": item_type, "Price": fee, "Status": "Charging"}])
            cust_df = pd.concat([cust_df, new_row], ignore_index=True)
            cust_df.to_csv(DB_FILES["cust"], index=False)
            st.success("Saved Successfully!")
            st.rerun()

    st.subheader("📋 Active Queue")
    active = cust_df[cust_df['Status'] == "Charging"] if not cust_df.empty else pd.DataFrame()
    if not active.empty:
        st.dataframe(active, use_container_width=True)
        for i, row in active.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**Card {row['Card']}** | {row['Name']}")
            if c2.button("Confirm Collection", key=f"coll_{i}"):
                cust_df.at[i, 'Status'] = "Collected ✅"
                cust_df.to_csv(DB_FILES["cust"], index=False)
                st.rerun()
    else: st.info("No phones are currently charging.")

# --- 6. RETAIL & POS (ADMIN ONLY) ---
elif choice == "🛒 Retail & POS":
    st.header("📦 Inventory & Sales")
    if st.session_state.auth == "admin":
        with st.expander("➕ Admin: Add New Stock"):
            n_item = st.text_input("Item Name")
            n_price = st.number_input("Selling Price", 0.0)
            n_qty = st.number_input("Quantity", 1)
            if st.button("Add to Inventory"):
                new_inv = pd.DataFrame([{"Item": n_item, "Price": n_price, "Stock": n_qty, "Cost": 0.0}])
                inv_df = pd.concat([inv_df, new_inv], ignore_index=True)
                inv_df.to_csv(DB_FILES["inv"], index=False); st.rerun()

# --- 7. MASTER CONTROL (ADMIN ONLY) ---
elif choice == "⚙️ Master Control":
    if st.session_state.auth == "admin":
        st.header("🔐 Master Controller")
        if st.button("♻️ CLEAR ALL HISTORY"):
            for key in ["cust", "maint", "missing"]:
                pd.DataFrame().to_csv(DB_FILES[key], index=False)
            st.success("History Wiped!")
            st.rerun()
    else: st.error("Admin Only Access")
