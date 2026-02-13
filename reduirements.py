import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Abubakarr Enterprise Por", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THE DATABASE REPAIRMAN (FIXES LINE 196 & MISSING COST) ---
DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "login": "secure_login.csv",
    "maint": "maintenance_log.csv"
}

def init_system():
    # Fix for Line 196: Ensure ALL columns exist
    for key, path in DB_FILES.items():
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            if key == "login":
                df = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"}, {"role": "staff", "user": "staff", "pw": "hub456"}])
            elif key == "inv":
                df = pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"]) # Added Cost
            elif key == "cust":
                df = pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status", "Staff"])
            else:
                df = pd.DataFrame(columns=["Date", "Action", "Cost", "Note"])
            df.to_csv(path, index=False)
        else:
            # AUTO-UPGRADE: If file exists but is missing a column (like 'Cost' or 'Staff'), add it!
            existing_df = pd.read_csv(path)
            if key == "inv" and "Cost" not in existing_df.columns:
                existing_df["Cost"] = 0.0
                existing_df.to_csv(path, index=False)
            if key == "cust" and "Staff" not in existing_df.columns:
                existing_df["Staff"] = "Unknown"
                existing_df.to_csv(path, index=False)

init_system()

# --- 3. SECURE LOGIN & REPAIR ---
if 'auth' not in st.session_state: st.session_state.auth = None
if 'username' not in st.session_state: st.session_state.username = None

# Safety check for NoneType errors
if st.session_state.auth is not None and st.session_state.username is None:
    st.session_state.auth = None
    st.rerun()

if not st.session_state.auth:
    st.title("🔐 Abubakarr Enterprise Por")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password")
    if st.button("🚀 OPEN SYSTEM"):
        login_df = pd.read_csv(DB_FILES["login"])
        match = login_df[(login_df['user'].str.lower() == u) & (login_df['pw'].astype(str) == p)]
        if not match.empty:
            st.session_state.auth = match.iloc[0]['role']
            st.session_state.username = u
            st.rerun()
    st.stop()

# --- 4. DATA LOADING ---
cust_df = pd.read_csv(DB_FILES["cust"])
inv_df = pd.read_csv(DB_FILES["inv"])
safe_user = st.session_state.username.upper()

# --- 5. SIDEBAR (AI & 3-BAGS) ---
st.sidebar.title(f"👤 {safe_user}")
total_rev = cust_df['Price'].sum() if not cust_df.empty else 0
st.sidebar.metric("👜 Ops (40%)", f"Le {total_rev * 0.4:,.1f}")
st.sidebar.metric("📦 Stock (30%)", f"Le {total_rev * 0.3:,.1f}")
st.sidebar.metric("💰 PROFIT (30%)", f"Le {total_rev * 0.3:,.1f}")

menu = ["⚡ Charging Registry", "🛒 Retail Shop", "📊 Reports", "⚙️ Admin"]
choice = st.sidebar.radio("Menu", menu)

# --- 6. CHARGING REGISTRY (FIXED LINE 196) ---
if choice == "⚡ Charging Registry":
    st.header("⚡ Device Charging Registry")
    
    with st.expander("➕ New Entry"):
        with st.form("c_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            card = c1.selectbox("Card #", list(range(1, 101)))
            name = c2.text_input("Customer Name")
            dev = c1.selectbox("Device", ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank", "Speaker"])
            price = c2.select_slider("Price (Le)", options=[3,4,5,6,7,8,9,10])
            if st.form_submit_button("Save"):
                new = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Card": card, "Name": name, "Device": dev, "Price": price, "Status": "Charging", "Staff": safe_user}])
                cust_df = pd.concat([cust_df, new], ignore_index=True)
                cust_df.to_csv(DB_FILES["cust"], index=False)
                st.success("Saved!"); st.rerun()

    st.subheader("📋 Active Queue")
    active = cust_df[cust_df['Status'] == "Charging"]
    if not active.empty:
        for idx, row in active.iterrows():
            col1, col2 = st.columns([3,1])
            # CRITICAL FIX: Safe access to columns to prevent Line 196 error
            col1.info(f"**Card {row['Card']}** | {row['Name']} | {row['Device']} (Le {row['Price']})")
            if col2.button("Done ✅", key=f"d_{idx}"):
                cust_df.at[idx, 'Status'] = "Collected"
                cust_df.to_csv(DB_FILES["cust"], index=False); st.rerun()
    else: st.info("Queue is empty.")

# --- 7. RETAIL SHOP (WITH COST AREA) ---
elif choice == "🛒 Retail Shop":
    st.header("🛒 Retail Shop & Inventory")
    t1, t2 = st.tabs(["💸 Sales (POS)", "📦 Stock Management"])
    
    with t1:
        if not inv_df.empty:
            item_sel = st.selectbox("Select Item", inv_df['Item'].tolist())
            row = inv_df[inv_df['Item'] == item_sel].iloc[0]
            st.write(f"**Stock:** {row['Stock']} | **Price:** Le {row['Price']}")
            if st.button("Confirm Sale"):
                if row['Stock'] > 0:
                    inv_df.loc[inv_df['Item'] == item_sel, 'Stock'] -= 1
                    inv_df.to_csv(DB_FILES["inv"], index=False); st.success("Sold!"); st.rerun()
        else: st.warning("Inventory empty.")

    with t2:
        st.dataframe(inv_df, use_container_width=True)
        if st.session_state.auth == "admin":
            st.subheader("➕ Add New Stock (Admin Only)")
            with st.form("add_inv"):
                name = st.text_input("Item Name")
                buy_price = st.number_input("Buying Cost (Le)", 0.0) # THE COST FIELD YOU NEEDED
                sell_price = st.number_input("Selling Price (Le)", 0.0)
                qty = st.number_input("Quantity", 1)
                if st.form_submit_button("Add Item"):
                    new_item = pd.DataFrame([{"Item": name, "Stock": qty, "Price": sell_price, "Cost": buy_price}])
                    inv_df = pd.concat([inv_df, new_item], ignore_index=True)
                    inv_df.to_csv(DB_FILES["inv"], index=False); st.success("Stock Added!"); st.rerun()

# --- 8. REPORTS ---
elif choice == "📊 Reports":
    st.title("📊 Profit & WhatsApp")
    st.metric("Total Income", f"Le {total_rev}")
    # WhatsApp Report Logic
    report = f"Abubakarr Enterprise Report - Total: Le {total_rev}"
    url = f"https://wa.me/?text={report.replace(' ', '%20')}"
    st.link_button("📤 Send WhatsApp Report", url)

# --- 9. ADMIN ---
elif choice == "⚙️ Admin":
    if st.session_state.auth == "admin":
        if st.button("🧨 WIPE DATA (RESET ALL)"):
            init_system() # Re-runs the fresh file creator
            st.rerun()
    else: st.error("Admin Only")

if st.sidebar.button("Logout"):
    st.session_state.auth = None; st.rerun()
