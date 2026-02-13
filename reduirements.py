import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CORE SYSTEM & AUTO-REPAIR ENGINE ---
st.set_page_config(page_title="Abubakarr Enterprise Por", layout="wide", initial_sidebar_state="collapsed")

DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "logins": "access_control.csv",
    "maint": "maintenance.csv"
}

def bootstrap_system():
    """Fixes files and prevents EmptyDataErrors before they happen."""
    for key, path in DB_FILES.items():
        # If file is missing or empty, build it from scratch
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            if key == "logins":
                df = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"},
                                   {"role": "staff", "user": "staff", "pw": "hub456"}])
            elif key == "inv":
                df = pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"])
            elif key == "cust":
                df = pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status"])
            else:
                df = pd.DataFrame(columns=["Date", "Action", "Cost"])
            df.to_csv(path, index=False)

bootstrap_system()

# --- 2. DATA LOAD ---
cust_df = pd.read_csv(DB_FILES["cust"])
inv_df = pd.read_csv(DB_FILES["inv"])
login_df = pd.read_csv(DB_FILES["logins"])

# --- 3. SECURE LOGIN (MOBILE OPTIMIZED) ---
if 'auth' not in st.session_state: st.session_state.auth = None

if not st.session_state.auth:
    st.title("🏙️ Abubakarr Enterprise Por")
    st.subheader("Master Access Control")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("🔓 Open Dashboard"):
        match = login_df[(login_df['user'].str.lower() == u) & (login_df['pw'].astype(str) == p)]
        if not match.empty:
            st.session_state.auth = match.iloc[0]['role']
            st.session_state.username = u
            st.rerun()
        else: st.error("Access Denied: Check details.")
    st.stop()

# --- 4. SIDEBAR (3-BAG SYSTEM & KRIO AI) ---
st.sidebar.title("💎 THE 3-BAGS")
total_revenue = cust_df['Price'].sum() if not cust_df.empty else 0
st.sidebar.info(f"👜 Bag 1 (Ops): Le {total_revenue * 0.4:.1f}")
st.sidebar.warning(f"👜 Bag 2 (Stock): Le {total_revenue * 0.3:.1f}")
st.sidebar.success(f"💰 Bag 3 (Wealth): Le {total_revenue * 0.3:.1f}")

st.sidebar.divider()
st.sidebar.write("🎙️ **Krio AI Assistant**")
if total_revenue > 200:
    st.sidebar.markdown("🗨️ *'De business de flow fine! Keep eye on de cards.'*")
else:
    st.sidebar.markdown("🗨️ *'Small small, we go reach. Check de device queue.'*")

menu = ["🏪 Charging Registry", "📦 Retail Shop", "🔧 Maintenance", "⚙️ Master Control"]
choice = st.sidebar.radio("Navigate", menu)

# --- 5. CHARGING REGISTRY (SIERRA LEONE DEVICES) ---
if choice == "🏪 Charging Registry":
    st.header("⚡ Master Charging Management")
    with st.form("charging_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        card_no = c1.selectbox("Card Number", list(range(0, 101)))
        cust_name = c2.text_input("Customer Name")
        device_list = ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank", "Speaker", "Tablet"]
        device = c1.selectbox("Select Device Type", device_list)
        price = c2.select_slider("Price (Le)", options=list(range(3, 11)))
        
        if st.form_submit_button("✅ Register Device"):
            new_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Card": card_no, 
                                       "Name": cust_name, "Device": device, "Price": price, "Status": "Charging"}])
            cust_df = pd.concat([cust_df, new_entry], ignore_index=True)
            cust_df.to_csv(DB_FILES["cust"], index=False)
            st.success(f"Saved! Card {card_no} is now Active.")
            st.rerun()

    st.subheader("📋 Current Charging Queue")
    active = cust_df[cust_df['Status'] == "Charging"]
    if not active.empty:
        st.dataframe(active[["Card", "Name", "Device", "Price"]], use_container_width=True)
        for i, row in active.iterrows():
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"🏷️ **Card {row['Card']}** | {row['Name']} ({row['Device']})")
            if col_b.button("Confirm Collection", key=f"coll_{i}"):
                cust_df.at[i, 'Status'] = "Collected ✅"
                cust_df.to_csv(DB_FILES["cust"], index=False)
                st.rerun()
    else: st.info("No phones are currently charging.")

# --- 6. RETAIL SHOP (ADMIN ONLY ADD STOCK) ---
elif choice == "📦 Retail Shop":
    st.header("🛒 Shop Inventory")
    if st.session_state.auth == "admin":
        with st.expander("➕ Admin: Add New Stock"):
            n_item = st.text_input("Item Name")
            n_price = st.number_input("Price", 0.0)
            n_qty = st.number_input("Quantity", 1)
            if st.button("Add Item"):
                new_item = pd.DataFrame([{"Item": n_item, "Stock": n_qty, "Price": n_price, "Cost": 0.0}])
                inv_df = pd.concat([inv_df, new_item], ignore_index=True)
                inv_df.to_csv(DB_FILES["inv"], index=False); st.rerun()
    
    st.subheader("Point of Sale")
    if not inv_df.empty:
        sell_item = st.selectbox("Sell Item", inv_df['Item'].tolist())
        if st.button("Complete Sale (Le)"):
            idx = inv_df.index[inv_df['Item'] == sell_item][0]
            if inv_df.at[idx, 'Stock'] > 0:
                inv_df.at[idx, 'Stock'] -= 1
                inv_df.to_csv(DB_FILES["inv"], index=False)
                st.success(f"Sale Recorded for {sell_item}!")
                st.rerun()
            else: st.error("Out of Stock!")
    else: st.info("Inventory is empty.")

# --- 7. MASTER CONTROL (ADMIN ONLY) ---
elif choice == "⚙️ Master Control":
    if st.session_state.auth == "admin":
        st.header("🔐 Master Controller")
        with st.expander("👤 User Management"):
            for idx, row in login_df.iterrows():
                st.write(f"User: {row['user']} | Role: {row['role']}")
            st.divider()
            new_user = st.text_input("New Staff Username")
            new_pass = st.text_input("New Staff Password")
            if st.button("Create Staff Account"):
                new_row = pd.DataFrame([{"role": "staff", "user": new_user, "pw": new_pass}])
                login_df = pd.concat([login_df, new_row], ignore_index=True)
                login_df.to_csv(DB_FILES["logins"], index=False); st.success("Account Created!")

        if st.button("♻️ WIPE ALL APP HISTORY"):
            pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status"]).to_csv(DB_FILES["cust"], index=False)
            st.success("App Data Cleared!"); st.rerun()
    else: st.error("Admin Only Access")

if st.sidebar.button("🚪 Logout"):
    st.session_state.auth = None
    st.rerun()
