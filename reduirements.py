import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime, timedelta

# --- 1. CORE ENGINE & OFFLINE SYNC ---
st.set_page_config(page_title="Abu Bakr Master Hub", layout="wide", initial_sidebar_state="collapsed")

DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "maint": "maintenance_log.csv",
    "missing": "missing_cards.csv",
    "login": "login_creds.csv",
    "sales": "sales_history.csv"
}

def init_db():
    for key, file in DB_FILES.items():
        if not os.path.exists(file):
            if key == "login":
                pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"}]).to_csv(file, index=False)
            elif key == "inv":
                pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"]).to_csv(file, index=False)
            else:
                pd.DataFrame().to_csv(file, index=False)

init_db()

# --- 2. STRONG SECURITY ENGINE ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("🛡️ Master Controller Login")
    u = st.text_input("Username").lower().strip() # Case-insensitive
    p = st.text_input("Password", type="password").strip()
    if st.button("Access System"):
        ldf = pd.read_csv(DB_FILES["login"])
        match = ldf[(ldf['user'].str.lower() == u) & (ldf['pw'].astype(str) == p)]
        if not match.empty:
            st.session_state.auth = match.iloc[0]['role']
            st.session_state.user = u
            st.rerun()
        else: st.error("Unauthorized Access Attempt Blocked")
    st.stop()

# --- 3. GLOBAL DATA LOADING ---
cust_df = pd.read_csv(DB_FILES["cust"])
inv_df = pd.read_csv(DB_FILES["inv"])
maint_df = pd.read_csv(DB_FILES["maint"])
login_df = pd.read_csv(DB_FILES["login"])

# --- 4. SIDEBAR (3-BAG SYSTEM & KRIO AI) ---
st.sidebar.title("💎 3-BAG SYSTEM")
total_revenue = cust_df['Price'].sum() if 'Price' in cust_df.columns else 0
st.sidebar.write(f"**Total Rev:** Le {total_revenue}")
st.sidebar.warning(f"Bag 1 (Ops): Le 124.0")
bag2 = st.sidebar.number_input("Bag 2 (Restock)", 0.0)
st.sidebar.success(f"Bag 3 (Wealth): Le {total_revenue - 124.0 - bag2 - 30}")

st.sidebar.divider()
st.sidebar.write("🧠 **AI Prediction (Krio):**")
if total_revenue > 100:
    st.sidebar.info("AI: 'De shop go boff today, prepare for customers!'")
else:
    st.sidebar.info("AI: 'Business slow small, check de area.'")

menu = ["🔌 Charging Registry", "🛒 Retail & POS", "🔧 Maint & Cards", "📊 AI Dashboard", "⚙️ Master Control"]
choice = st.sidebar.radio("Navigation", menu)

# --- 5. CHARGING REGISTRY (v10.0 UPGRADE) ---
if choice == "🔌 Charging Registry":
    st.header("⚡ Charging Management")
    with st.form("entry", clear_on_submit=True):
        col1, col2 = st.columns(2)
        card = col1.selectbox("Card Number", list(range(0, 101)))
        name = col2.text_input("Customer Name")
        item_type = col1.selectbox("Device Type", ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Power Bank", "Bluetooth Speaker", "Button Phone", "Tablet"])
        fee = col2.select_slider("Price (Le)", options=list(range(3, 11)))
        
        if st.form_submit_button("Register & Generate Receipt"):
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Card": card, "Name": name, "Item": item_type, "Price": fee, "Status": "Charging"}])
            cust_df = pd.concat([cust_df, new_row], ignore_index=True)
            cust_df.to_csv(DB_FILES["cust"], index=False)
            st.success("Entry Saved Offline & Online Sync Ready!")
            st.rerun()

    st.subheader("📋 Active Queue")
    if not cust_df.empty:
        active = cust_df[cust_df['Status'] == "Charging"]
        if not active.empty:
            st.dataframe(active, use_container_width=True)
            for i, row in active.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**Card {row['Card']}** | {row['Name']} ({row['Item']})")
                if c2.button("Confirm Collection", key=f"coll_{i}"):
                    cust_df.at[i, 'Status'] = "Collected ✅"
                    cust_df.to_csv(DB_FILES["cust"], index=False)
                    st.rerun()
        else:
            st.info("No phones are currently charging.")


# --- 6. RETAIL & POS (ADMIN ONLY ADDITION) ---
elif choice == "🛒 Retail & POS":
    st.header("📦 Inventory & Sales")
    if st.session_state.auth == "admin":
        with st.expander("➕ Admin: Add New Stock"):
            n_item = st.text_input("Item Name")
            n_cost = st.number_input("Cost Price", 0.0)
            n_price = st.number_input("Selling Price", 0.0)
            n_qty = st.number_input("Quantity", 1)
            if st.button("Add to Inventory"):
                inv_df = pd.concat([inv_df, pd.DataFrame([{"Item": n_item, "Cost": n_cost, "Price": n_price, "Stock": n_qty}])], ignore_index=True)
                inv_df.to_csv(DB_FILES["inv"], index=False); st.rerun()

    st.subheader("💸 Point of Sale")
    sell_item = st.selectbox("Select Item to Sell", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
    if st.button("Complete Sale & Print Receipt"):
        idx = inv_df.index[inv_df['Item'] == sell_item][0]
        if inv_df.at[idx, 'Stock'] > 0:
            inv_df.at[idx, 'Stock'] -= 1
            inv_df.to_csv(DB_FILES["inv"], index=False)
            st.success(f"Sold {sell_item}! Profit: Le {inv_df.at[idx, 'Price'] - inv_df.at[idx, 'Cost']}")

# --- 7. MASTER CONTROL (ADMIN ONLY) ---
elif choice == "⚙️ Master Control":
    if st.session_state.auth == "admin":
        st.header("🔐 Master Controller")
        
        with st.expander("👤 User & Password Management"):
            for idx, row in login_df.iterrows():
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"User: {row['user']} | Role: {row['role']}")
                if row['user'] != st.session_state.user:
                    if col_b.button("Remove", key=f"user_{idx}"):
                        login_df.drop(idx).to_csv(DB_FILES["login"], index=False); st.rerun()
            
            st.divider()
            new_u = st.text_input("New Username").lower()
            new_p = st.text_input("New Password")
            if st.button("Create New User"):
                pd.concat([login_df, pd.DataFrame([{"role": "staff", "user": new_u, "pw": new_p}])]).to_csv(DB_FILES["login"], index=False); st.rerun()

        if st.button("♻️ CLEAR ALL APP HISTORY"):
            for f in [DB_FILES["cust"], DB_FILES["maint"], DB_FILES["missing"]]:
                pd.DataFrame().to_csv(f, index=False)
            st.success("History Wiped!")

    else: st.error("Access Denied: Admin Only")
    if st.button("Access System"):
        ldf = pd.read_csv(DB_FILES["login"])
        match = ldf[(ldf['user'].str.lower() == u) & (ldf['pw'].astype(str) == p)]
        if not match.empty:
            st.session_state.auth = match.iloc[0]['role']
            st.session_state.user = u
            st.rerun()
        else: st.error("Unauthorized Access Attempt Blocked")
    st.stop()

# --- 3. GLOBAL DATA LOADING (FIXED FOR LINE 48) ---
def load_safe(key, cols):
    file_path = DB_FILES[key]
    # Check if file exists AND if it has data inside
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            return pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            # If it's still empty despite the check, fall through to create new
            pass
   
    # Create a fresh table if the file is missing or empty
    if key == "login":
        df = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"}])
    elif key == "inv":
        df = pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"])
    else:
        df = pd.DataFrame(columns=cols)
   
    df.to_csv(file_path, index=False)
    return df
# --- 4. SIDEBAR (3-BAG SYSTEM & KRIO AI) ---
st.sidebar.title("💎 3-BAG SYSTEM")
total_revenue = cust_df['Price'].sum() if 'Price' in cust_df.columns else 0
st.sidebar.write(f"**Total Rev:** Le {total_revenue}")
st.sidebar.warning(f"Bag 1 (Ops): Le 124.0")
bag2 = st.sidebar.number_input("Bag 2 (Restock)", 0.0)
st.sidebar.success(f"Bag 3 (Wealth): Le {total_revenue - 124.0 - bag2 - 30}")

st.sidebar.divider()
st.sidebar.write("🧠 **AI Prediction (Krio):**")
if total_revenue > 100:
    st.sidebar.info("AI: 'De shop go boff today, prepare for customers!'")
else:
    st.sidebar.info("AI: 'Business slow small, check de area.'")

menu = ["🔌 Charging Registry", "🛒 Retail & POS", "🔧 Maint & Cards", "📊 AI Dashboard", "⚙️ Master Control"]
choice = st.sidebar.radio("Navigation", menu)

# --- 5. CHARGING REGISTRY (v10.0 UPGRADE) ---
if choice == "🔌 Charging Registry":
    st.header("⚡ Charging Management")
    with st.form("entry", clear_on_submit=True):
        col1, col2 = st.columns(2)
        card = col1.selectbox("Card Number", list(range(0, 101)))
        name = col2.text_input("Customer Name")
        item_type = col1.selectbox("Device Type", ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Power Bank", "Bluetooth Speaker", "Button Phone", "Tablet"])
        fee = col2.select_slider("Price (Le)", options=list(range(3, 11)))
        if st.form_submit_button("Register & Generate Receipt"):
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Card": card, "Name": name, "Item": item_type, "Price": fee, "Status": "Charging"}])
            cust_df = pd.concat([cust_df, new_row], ignore_index=True)
            cust_df.to_csv(DB_FILES["cust"], index=False)
            st.success("Entry Saved Offline & Online Sync Ready!")

    st.subheader("📋 Active Queue")
    if not cust_df.empty:
        active = cust_df[cust_df['Status'] == "Charging"]
        st.dataframe(active, use_container_width=True)
        for i, row in active.iterrows():
            c1, c2 = st.columns([3, 1])
            c1.write(f"**Card {row['Card']}** | {row['Name']} ({row['Item']})")
            if c2.button("Confirm Collection", key=f"coll_{i}"):
                cust_df.at[i, 'Status'] = "Collected ✅"
                cust_df.to_csv(DB_FILES["cust"], index=False)
                st.rerun()

# --- 6. RETAIL & POS (ADMIN ONLY ADDITION) ---
elif choice == "🛒 Retail & POS":
    st.header("📦 Inventory & Sales")
    if st.session_state.auth == "admin":
        with st.expander("➕ Admin: Add New Stock"):
            n_item = st.text_input("Item Name")
            n_cost = st.number_input("Cost Price", 0.0)
            n_price = st.number_input("Selling Price", 0.0)
            n_qty = st.number_input("Quantity", 1)
            if st.button("Add to Inventory"):
                inv_df = pd.concat([inv_df, pd.DataFrame([{"Item": n_item, "Cost": n_cost, "Price": n_price, "Stock": n_qty}])], ignore_index=True)
                inv_df.to_csv(DB_FILES["inv"], index=False); st.rerun()

    st.subheader("💸 Point of Sale")
    sell_item = st.selectbox("Select Item to Sell", inv_df['Item'].tolist() if not inv_df.empty else ["No Stock"])
    if st.button("Complete Sale & Print Receipt"):
        idx = inv_df.index[inv_df['Item'] == sell_item][0]
        if inv_df.at[idx, 'Stock'] > 0:
            inv_df.at[idx, 'Stock'] -= 1
            inv_df.to_csv(DB_FILES["inv"], index=False)
            st.success(f"Sold {sell_item}! Profit: Le {inv_df.at[idx, 'Price'] - inv_df.at[idx, 'Cost']}")

# --- 7. MASTER CONTROL (ADMIN ONLY) ---
elif choice == "⚙️ Master Control":
    if st.session_state.auth == "admin":
        st.header("🔐 Master Controller")
       
        with st.expander("👤 User & Password Management"):
            for idx, row in login_df.iterrows():
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"User: {row['user']} | Role: {row['role']}")
                if row['user'] != st.session_state.user:
                    if col_b.button("Remove", key=f"user_{idx}"):
                        login_df.drop(idx).to_csv(DB_FILES["login"], index=False); st.rerun()
           
            st.divider()
            new_u = st.text_input("New Username").lower()
            new_p = st.text_input("New Password")
            if st.button("Create New User"):
                pd.concat([login_df, pd.DataFrame([{"role": "staff", "user": new_u, "pw": new_p}])]).to_csv(DB_FILES["login"], index=False); st.rerun()

        if st.button("♻️ CLEAR ALL APP HISTORY"):
            for f in [DB_FILES["cust"], DB_FILES["maint"], DB_FILES["missing"]]:
                pd.DataFrame().to_csv(f, index=False)
            st.success("History Wiped!")

    else: st.error("Access Denied: Admin Only")


