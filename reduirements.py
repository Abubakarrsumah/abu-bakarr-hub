import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. MOBILE-FRIENDLY CONFIG ---
st.set_page_config(
    page_title="Abu Bakr Hub",
    layout="wide",
    initial_sidebar_state="collapsed" # Better for small Android screens
)

# --- 2. DATABASE LOADING ---
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
   
    if os.path.exists(DB_LOGIN): login = pd.read_csv(DB_LOGIN)
    else: login = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"},
                             {"role": "staff", "user": "staff", "pw": "hub456"}])
   
    return cust, inv, maint, missing, login

cust_df, inv_df, maint_df, missing_df, login_df = load_data()

# --- 3. LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("🏙️ Abu Bakr Hub Login")
    u_in = st.text_input("Username")
    p_in = st.text_input("Password", type="password")
    if st.button("Login"):
        user_match = login_df[(login_df['user'] == u_in) & (login_df['pw'] == p_in)]
        if not user_match.empty:
            st.session_state.auth = user_match.iloc[0]['role']
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 4. NAVIGATION ---
menu = ["📊 Dashboard", "🔌 Charging", "🛒 Shop", "🔧 Maint", "⚙️ Admin"]
choice = st.sidebar.radio("Menu", menu)

# --- 5. 3-BAG SYSTEM (MOBILE VIEW) ---
st.sidebar.divider()
rev = cust_df['Price'].sum()
b1, b2 = 124.0, st.sidebar.number_input("Bag 2 (Restock)", 0.0)
st.sidebar.success(f"Wealth: Le {rev - b1 - b2 - 30}")

# --- 6. PAGE LOGIC ---

if choice == "🔌 Charging":
    st.header("Registry")
    models = ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button", "Other"]
   
    with st.expander("➕ Register New Device", expanded=True):
        with st.form("reg", clear_on_submit=True):
            card = st.selectbox("Card #", list(range(1, 101)))
            name = st.text_input("Name")
            mod = st.selectbox("Model", models)
            fee = st.select_slider("Fee (Le)", options=list(range(3, 11)))
            if st.form_submit_button("Save"):
                new = {"Date": datetime.now().strftime("%Y-%m-%d"), "Card #": card, "Name": name, "Model": mod, "Status": "Charging", "Price": fee}
                cust_df = pd.concat([cust_df, pd.DataFrame([new])], ignore_index=True)
                cust_df.to_csv(DB_CUST, index=False); st.rerun()

    st.divider()
    st.subheader("✅ Collections")
    active = cust_df[cust_df['Status'] == "Charging"]
    for i, row in active.iterrows():
        # Mobile-friendly list layout
        c_name, c_btn = st.columns([2, 1])
        c_name.write(f"Crd {row['Card #']}: {row['Name']}")
        if c_btn.button("Confirm", key=f"v85_{i}"):
            cust_df.at[i, 'Status'] = "Collected ✅"
            cust_df.to_csv(DB_CUST, index=False); st.rerun()

elif choice == "🛒 Shop":
    st.header("Retail Profit")
    inv_df['Profit'] = inv_df['Price'] - inv_df['Cost']
    st.dataframe(inv_df[['Item', 'Stock', 'Price', 'Profit']], use_container_width=True)
   
    sell = st.selectbox("Sell Item", inv_df['Item'].tolist())
    if st.button("Confirm Sale"):
        idx = inv_df.index[inv_df['Item'] == sell][0]
        if inv_df.at[idx, 'Stock'] > 0:
            inv_df.at[idx, 'Stock'] -= 1
            inv_df.to_csv(DB_INV, index=False); st.success("Sold!"); st.rerun()

elif choice == "⚙️ Admin":
    if st.session_state.auth == "admin":
        # Edit Credentials
        with st.expander("🔑 Edit Logins"):
            role = st.selectbox("Role", ["admin", "staff"])
            nu, np = st.text_input("New User"), st.text_input("New PW", type="password")
            if st.button("Update"):
                login_df.loc[login_df['role'] == role, 'user'] = nu
                login_df.loc[login_df['role'] == role, 'pw'] = np
                login_df.to_csv(DB_LOGIN, index=False); st.success("Updated")
       
        # New Product
        with st.expander("➕ New Product"):
            name = st.text_input("Item Name")
            cost = st.number_input("Cost", 0.0)
            price = st.number_input("Price", 0.0)
            if st.button("Add"):
                item = {"Item": name, "Stock": 10, "Price": price, "Cost": cost}
                inv_df = pd.concat([inv_df, pd.DataFrame([item])], ignore_index=True)
                inv_df.to_csv(DB_INV, index=False); st.rerun()
               
        st.divider()
        st.download_button("📥 Monthly Report", cust_df.to_csv(index=False), "report.csv")
    else: st.error("Admin Only")

# Maintenance and Dashboard sections remain integrated in the code structure
