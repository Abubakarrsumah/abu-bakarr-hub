import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Abubakarr Enterprise Por",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. THE DATABASE ENGINE (WITH AUTO-REPAIR FOR ERRORS) ---
DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "login": "secure_login.csv",
    "maint": "maintenance_log.csv"
}

def init_system():
    """Ensures files exist and have the correct columns to prevent KeyErrors."""
    for key, path in DB_FILES.items():
        # Define correct columns for each file
        if key == "login":
            cols = ["role", "user", "pw"]
            default_data = [{"role": "admin", "user": "admin", "pw": "abu123"}]
        elif key == "inv":
            cols = ["Item", "Stock", "Price", "Cost"] # Added Cost
            default_data = []
        elif key == "cust":
            cols = ["Date", "Card", "Name", "Device", "Price", "Status", "Staff"]
            default_data = []
        else:
            cols = ["Date", "Action", "Cost", "Note"]
            default_data = []

        # Create file if it doesn't exist
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            pd.DataFrame(default_data, columns=cols).to_csv(path, index=False)
        else:
            # AUTO-REPAIR: If file exists but is missing a column, fix it now!
            df = pd.read_csv(path)
            missing = [c for c in cols if c not in df.columns]
            if missing:
                for m in missing:
                    df[m] = 0 if m in ["Price", "Cost", "Stock"] else "N/A"
                df.to_csv(path, index=False)

init_system()

# --- 3. DATA LOADING ---
def get_data(key): return pd.read_csv(DB_FILES[key])
def save_data(key, df): df.to_csv(DB_FILES[key], index=False)

# Load data safely
cust_df = get_data("cust")
inv_df = get_data("inv")
login_df = get_data("login")

# --- 4. SECURE LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = None
if 'username' not in st.session_state: st.session_state.username = None

# Safety check for Line 86 Error
if st.session_state.auth is not None and st.session_state.username is None:
    st.session_state.auth = None
    st.rerun()

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🔐 Abubakarr Enterprise</h1>", unsafe_allow_html=True)
    with st.container():
        _, c2, _ = st.columns([1, 2, 1])
        with c2:
            u = st.text_input("Username").lower().strip()
            p = st.text_input("Password", type="password")
            if st.button("🚀 ACCESS SYSTEM", use_container_width=True):
                match = login_df[(login_df['user'].str.lower() == u) & (login_df['pw'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth = match.iloc[0]['role']
                    st.session_state.username = u
                    st.rerun()
    st.stop()

# --- 5. SIDEBAR ---
safe_user = st.session_state.username.upper()
st.sidebar.markdown(f"## 👤 {safe_user}")
total_income = cust_df['Price'].sum() if not cust_df.empty else 0
st.sidebar.metric("💰 TOTAL REVENUE", f"Le {total_income:,.0f}")
st.sidebar.markdown("---")

menu = ["⚡ Charging Registry", "🛒 Retail Shop", "📊 Dashboard", "⚙️ Admin"]
choice = st.sidebar.radio("Navigation", menu)

if st.sidebar.button("🚪 Logout"):
    st.session_state.auth = None
    st.rerun()

# --- 6. CHARGING REGISTRY (FIXED KEYERROR & ADDED TABLE) ---
if choice == "⚡ Charging Registry":
    st.header("⚡ Device Charging Registry")
    
    with st.expander("➕ Register New Device", expanded=True):
        with st.form("charge_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            card = c1.selectbox("🎫 Card Number", list(range(1, 101)))
            name = c2.text_input("👤 Customer Name")
            device = c1.selectbox("📱 Device Type", ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank"])
            price = c2.select_slider("💵 Price (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10, 15, 20])
            
            if st.form_submit_button("✅ CHECK-IN"):
                new_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Card": card, "Name": name, 
                           "Device": device, "Price": price, "Status": "Charging", "Staff": safe_user}
                cust_df = pd.concat([cust_df, pd.DataFrame([new_row])], ignore_index=True)
                save_data("cust", cust_df)
                st.success("Entry Saved!")
                st.rerun()

    st.divider()
    st.subheader("📋 Active Queue (Pending Collection)")
    active_df = cust_df[cust_df['Status'] == "Charging"]
    
    if not active_df.empty:
        for idx, row in active_df.iterrows():
            col1, col2 = st.columns([4, 1])
            # FIXED: Safe column access to prevent KeyError
            col1.info(f"**Card {row.get('Card', '??')}** | {row.get('Name', 'Unknown')} | {row.get('Device', 'Device')} (Le {row.get('Price', 0)})")
            if col2.button("Done ✅", key=f"done_{idx}"):
                cust_df.at[idx, 'Status'] = "Collected"
                save_data("cust", cust_df)
                st.rerun()
    else:
        st.info("No devices currently charging.")

    st.divider()
    st.subheader("📜 All Charging Records (History)")
    st.dataframe(cust_df, use_container_width=True) # THIS IS THE TABLE YOU REQUESTED

# --- 7. RETAIL SHOP (WITH COST AREA) ---
elif choice == "🛒 Retail Shop":
    st.header("🛒 Retail Shop POS")
    t1, t2 = st.tabs(["💸 Sell Item", "📦 Stock List & Add Stock"])
    
    with t1:
        if not inv_df.empty:
            sell_item = st.selectbox("Select Item to Sell", inv_df['Item'].unique())
            item_row = inv_df[inv_df['Item'] == sell_item].iloc[0]
            st.info(f"**In Stock:** {item_row['Stock']} | **Price:** Le {item_row['Price']}")
            
            if st.button("💰 COMPLETE SALE"):
                if item_row['Stock'] > 0:
                    idx = inv_df.index[inv_df['Item'] == sell_item][0]
                    inv_df.at[idx, 'Stock'] -= 1
                    save_data("inv", inv_df)
                    st.success(f"Sold 1 {sell_item}!")
                    st.rerun()
                else:
                    st.error("Out of stock!")
        else:
            st.warning("No items in inventory.")

    with t2:
        st.subheader("📦 Inventory Overview")
        st.dataframe(inv_df, use_container_width=True) # SHOWS COST COLUMN
        
        if st.session_state.auth == "admin":
            st.markdown("---")
            st.subheader("➕ Add New Stock (Admin)")
            with st.form("add_stock_form"):
                c1, c2 = st.columns(2)
                i_name = c1.text_input("Item Name")
                i_qty = c2.number_input("Quantity", 1)
                i_cost = c1.number_input("Buying Cost (Le)", 0.0) # THE COST AREA YOU REQUESTED
                i_price = c2.number_input("Selling Price (Le)", 0.0)
                
                if st.form_submit_button("Add to Inventory"):
                    new_item = {"Item": i_name, "Stock": i_qty, "Price": i_price, "Cost": i_cost}
                    inv_df = pd.concat([inv_df, pd.DataFrame([new_item])], ignore_index=True)
                    save_data("inv", inv_df)
                    st.success(f"Added {i_name} to stock!")
                    st.rerun()

# --- 8. DASHBOARD & ADMIN ---
elif choice == "📊 Dashboard":
    st.title("📊 Business Reports")
    st.metric("Total Revenue", f"Le {total_income}")
    st.write("Full Report History:")
    st.dataframe(cust_df)

elif choice == "⚙️ Admin":
    if st.session_state.auth == "admin":
        st.subheader("🔐 Master Control")
        if st.button("♻️ RESET ALL DATA (Wipe Everything)"):
            init_system()
            st.rerun()
    else:
        st.error("Admin Only Access")
