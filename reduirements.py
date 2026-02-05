import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & DATABASE ---
st.set_page_config(page_title="Abu Bakr Enterprise Hub", layout="wide")

DB_CUST = "customer_data.csv"
DB_INV = "inventory_data.csv"
DB_MAINT = "maintenance_log.csv"
DB_MISSING = "missing_cards.csv"
DB_LOGIN = "login_creds.csv"

def load_data():
    if os.path.exists(DB_CUST): cust = pd.read_csv(DB_CUST)
    else: cust = pd.DataFrame(columns=["Date", "Card #", "Name", "Model", "Status", "Price"])
   
    if os.path.exists(DB_INV): inv = pd.read_csv(DB_INV)
    else: inv = pd.DataFrame([{"Item": "Water 💦", "Stock": 60, "Price": 1.0, "Cost": 0.5}])
   
    if os.path.exists(DB_MAINT): maint = pd.read_csv(DB_MAINT)
    else: maint = pd.DataFrame(columns=["Date", "Action", "Cost", "Next Due"])
   
    if os.path.exists(DB_MISSING): missing = pd.read_csv(DB_MISSING)
    else: missing = pd.DataFrame(columns=["Date", "Card #", "Reason", "Staff"])
   
    # Login Credentials
    if os.path.exists(DB_LOGIN): login = pd.read_csv(DB_LOGIN)
    else:
        login = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"},
                             {"role": "staff", "user": "staff", "pw": "hub456"}])
   
    return cust, inv, maint, missing, login

cust_df, inv_df, maint_df, missing_df, login_df = load_data()

# --- 2. LOGIN SYSTEM ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("🏙️ Abu Bakr Enterprise Login")
    u_input = st.text_input("Username")
    p_input = st.text_input("Password", type="password")
    if st.button("Login"):
        user_match = login_df[(login_df['user'] == u_input) & (login_df['pw'] == p_input)]
        if not user_match.empty:
            st.session_state.auth = user_match.iloc[0]['role']
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 3. SIDEBAR: 3-BAG SYSTEM ---
st.sidebar.title(f"🚀 {st.session_state.auth.upper()} PORTAL")
st.sidebar.divider()
st.sidebar.header("💰 3-Bag System")
total_rev = cust_df['Price'].sum()
bag1_ops = 124.0
bag2_restock = st.sidebar.number_input("Bag 2: Restock Money (Le)", min_value=0.0)
bag3_wealth = total_rev - bag1_ops - bag2_restock - 30
st.sidebar.success(f"💎 Bag 3 (Wealth): Le {max(0.0, bag3_wealth)}")

if st.sidebar.button("Logout"): st.session_state.auth = None; st.rerun()

menu = ["📊 Dashboard", "🔌 Charging Registry", "🛒 Retail Shop", "🔧 Maintenance", "🚨 Missing Cards", "⚙️ Admin Tools"]
choice = st.sidebar.radio("Go To:", menu)

# --- 4. APP PAGES ---

if choice == "📊 Dashboard":
    st.header("📈 Business Performance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Charging Revenue", f"Le {total_rev}")
    # Retail Profit Logic
    retail_rev = (inv_df['Price'] * 0).sum() # Placeholder for actual sales log
    c2.metric("Retail Items in Stock", len(inv_df))
    c3.metric("Maintenance Spend", f"Le {maint_df['Cost'].sum()}")

elif choice == "🔌 Charging Registry":
    st.subheader("📝 1. New Entry")
    # Phone Database
    phone_models = ["Infinix Hot", "Infinix Note", "Tecno Spark", "Tecno Camon", "Samsung A-Series", "Samsung S-Series", "iPhone", "Itel", "Redmi", "Huawei", "Nokia", "Button Phone", "Other"]
   
    with st.form("reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        # Upgrade: Card 1-100 selection
        card = col1.selectbox("Card #", list(range(1, 101)))
        name = col2.text_input("Customer Name")
        # Upgrade: Selectable Phone Models
        model = col1.selectbox("Phone Model", phone_models)
        # Upgrade: Fee 3 to 10 Le
        fee = col2.select_slider("Select Fee (Le)", options=list(range(3, 11)))
       
        if st.form_submit_button("Save Entry"):
            new_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Card #": card, "Name": name, "Model": model, "Status": "Charging", "Price": fee}
            cust_df = pd.concat([cust_df, pd.DataFrame([new_row])], ignore_index=True)
            cust_df.to_csv(DB_CUST, index=False); st.success("Saved!"); st.rerun()
   
    st.divider()
    st.subheader("📋 2. Active List & ✅ 3. Collection")
    active = cust_df[cust_df['Status'] == "Charging"]
    st.dataframe(active, use_container_width=True)
   
    search = st.text_input("🔍 Search to Confirm Collection")
    if search:
        active = active[active.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
   
    for i, row in active.iterrows():
        if st.button(f"Confirm Collection: Card {row['Card #']} ({row['Name']})", key=f"coll_{i}"):
            cust_df.at[i, 'Status'] = "Collected ✅"
            cust_df.to_csv(DB_CUST, index=False); st.rerun()

elif choice == "🛒 Retail Shop":
    st.header("🛒 Retail Inventory & Performance")
    # Upgrade: Show Cost and Potential Profit
    display_df = inv_df.copy()
    display_df['Unit Profit'] = display_df['Price'] - display_df['Cost']
    display_df['Total Potential Profit'] = display_df['Unit Profit'] * display_df['Stock']
    st.dataframe(display_df, use_container_width=True)
   
    st.divider()
    item = st.selectbox("Record Sale", inv_df['Item'].tolist())
    if st.button("Confirm Sale"):
        idx = inv_df.index[inv_df['Item'] == item][0]
        if inv_df.at[idx, 'Stock'] > 0:
            inv_df.at[idx, 'Stock'] -= 1
            inv_df.to_csv(DB_INV, index=False); st.success(f"Sold {item}! Profit: Le {inv_df.at[idx, 'Price'] - inv_df.at[idx, 'Cost']}"); st.rerun()

elif choice == "⚙️ Admin Tools":
    if st.session_state.auth == "admin":
        st.header("🔐 Admin Controls")
       
        # Upgrade: Change Login Details
        with st.expander("🔑 Change Login Credentials"):
            target_role = st.selectbox("Select Role to Update", ["admin", "staff"])
            new_user = st.text_input("New Username")
            new_pw = st.text_input("New Password", type="password")
            if st.button("Update Credentials"):
                login_df.loc[login_df['role'] == target_role, 'user'] = new_user
                login_df.loc[login_df['role'] == target_role, 'pw'] = new_pw
                login_df.to_csv(DB_LOGIN, index=False)
                st.success(f"Credentials for {target_role} updated!")

        with st.expander("➕ Add Inventory"):
            n_name = st.text_input("Item Name")
            n_stk = st.number_input("Qty", 1)
            n_cost = st.number_input("Cost Price (What you paid)", 0.1)
            n_prc = st.number_input("Selling Price (Le)", 0.2)
            if st.button("Add to Shop"):
                new_item = {"Item": n_name, "Stock": n_stk, "Price": n_prc, "Cost": n_cost}
                inv_df = pd.concat([inv_df, pd.DataFrame([new_item])], ignore_index=True)
                inv_df.to_csv(DB_INV, index=False); st.rerun()
               
        st.divider()
        st.download_button("📥 Download Master Report", cust_df.to_csv(index=False), "master_report.csv")
    else: st.error("Admin Only")

# (Other sections like Maintenance and Missing Cards remain exactly as per v8.3)
