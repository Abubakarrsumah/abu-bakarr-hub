import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time

# --- 1. APP CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="Abubakarr Enterprise Por",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# --- 2. THE "FORTRESS" DATA ENGINE ---
# Prevents "EmptyDataError" by auto-repairing files
DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "login": "secure_login.csv",
    "maint": "maintenance_log.csv"
}

def init_system():
    """Checks and repairs all database files before the app starts."""
    for key, path in DB_FILES.items():
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            # Auto-Repair: Create fresh files with correct headers
            if key == "login":
                # DEFAULT LOGIN: Admin (Master) and Staff (Worker)
                df = pd.DataFrame([
                    {"role": "admin", "user": "admin", "pw": "abu123"},
                    {"role": "staff", "user": "staff", "pw": "hub456"}
                ])
            elif key == "inv":
                df = pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"])
            elif key == "cust":
                df = pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status", "Staff"])
            else:
                df = pd.DataFrame(columns=["Date", "Action", "Cost", "Note"])
            df.to_csv(path, index=False)

init_system()

# --- 3. DATA LOADING ---
def get_data(key):
    return pd.read_csv(DB_FILES[key])

def save_data(key, df):
    df.to_csv(DB_FILES[key], index=False)

# Load data into memory
cust_df = get_data("cust")
inv_df = get_data("inv")
login_df = get_data("login")
maint_df = get_data("maint")

# --- 4. SECURE LOGIN & STATE REPAIR ---
# Initialize Session State
if 'auth' not in st.session_state: st.session_state.auth = None
if 'username' not in st.session_state: st.session_state.username = None

# FIX FOR LINE 86 ERROR: Auto-logout if state is corrupted
if st.session_state.auth is not None and st.session_state.username is None:
    st.session_state.auth = None
    st.rerun()

# Login Screen
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🔐 Abubakarr Enterprise Por</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Sierra Leone Master Hub</p>", unsafe_allow_html=True)
    
    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            u_input = st.text_input("👤 Username", placeholder="Enter ID...").lower().strip()
            p_input = st.text_input("🔑 Password", type="password", placeholder="Enter Pin...")
            
            if st.button("🚀 ACCESS DASHBOARD", use_container_width=True):
                user_match = login_df[(login_df['user'].str.lower() == u_input) & (login_df['pw'].astype(str) == p_input)]
                if not user_match.empty:
                    st.session_state.auth = user_match.iloc[0]['role']
                    st.session_state.username = u_input
                    st.toast(f"Welcome back, {u_input.upper()}!", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("⛔ ACCESS DENIED: Invalid Credentials")
    st.stop()

# --- 5. INTELLIGENT SIDEBAR ---
# Safe string handling to prevent crashes
safe_user = st.session_state.username if st.session_state.username else "User"
safe_role = st.session_state.auth if st.session_state.auth else "Staff"

st.sidebar.markdown(f"## 👤 {safe_user.upper()} ({safe_role.upper()})")

# 🧠 AI Krio Prediction
day_of_week = datetime.now().strftime("%A")
if day_of_week in ["Friday", "Saturday"]:
    ai_msg = "🔥 AI Says: 'Dis weekend go busy! Charge plenti power bank.'"
else:
    ai_msg = "📉 AI Says: 'Mid-week chill. Check stock level.'"
st.sidebar.info(ai_msg)

# 💰 3-Bag System Logic
total_income = cust_df['Price'].sum() if not cust_df.empty else 0
bag_ops = total_income * 0.4  # 40% for Operations
bag_restock = total_income * 0.3 # 30% for Stock
bag_wealth = total_income * 0.3 # 30% for Profit

st.sidebar.markdown("---")
st.sidebar.markdown("### 💎 3-BAGS WALLET")
st.sidebar.metric("👜 Ops (40%)", f"Le {bag_ops:,.1f}")
st.sidebar.metric("📦 Stock (30%)", f"Le {bag_restock:,.1f}")
st.sidebar.metric("💰 PROFIT (30%)", f"Le {bag_wealth:,.1f}")
st.sidebar.markdown("---")

# Navigation
if st.session_state.auth == "admin":
    menu = ["📊 Dashboard & WhatsApp", "⚡ Charging Registry", "🛒 Retail Shop", "🔧 Maintenance", "⚙️ Master Control"]
else:
    menu = ["⚡ Charging Registry", "🛒 Retail Shop"]

choice = st.sidebar.radio("Navigate", menu)
if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
    st.session_state.auth = None
    st.rerun()

# --- 6. DASHBOARD & WHATSAPP ---
if choice == "📊 Dashboard & WhatsApp":
    st.title("📊 Business Intelligence")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Revenue", f"Le {total_income}")
    kpi2.metric("Devices Charged", len(cust_df))
    val = (inv_df['Price'] * inv_df['Stock']).sum() if not inv_df.empty else 0
    kpi3.metric("Stock Value", f"Le {val}")
    
    st.divider()
    st.subheader("📲 WhatsApp Auto-Report")
    
    report_text = f"""
    *🏪 ABUBAKARR ENTERPRISE DAILY REPORT*
    📅 Date: {datetime.now().strftime('%Y-%m-%d')}
    
    *💰 FINANCE*
    - Total Sales: Le {total_income}
    - 3-Bags Profit: Le {bag_wealth}
    
    *⚡ CHARGING*
    - Total Devices: {len(cust_df)}
    
    *🧠 AI STATUS*
    - {ai_msg}
    
    *Signed: {safe_user.upper()}*
    """
    # Create WhatsApp Link
    whatsapp_url = f"https://wa.me/?text={report_text.replace(' ', '%20').replace(chr(10), '%0A')}"
    st.link_button("📤 Send Report via WhatsApp", whatsapp_url)

# --- 7. CHARGING REGISTRY ---
elif choice == "⚡ Charging Registry":
    st.header("⚡ Charging Station")
    
    with st.expander("➕ Register New Device", expanded=True):
        with st.form("charge_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            card = c1.selectbox("🎫 Card Number", list(range(1, 101)))
            name = c2.text_input("👤 Customer Name")
            dev_types = ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank", "Bluetooth Speaker", "Tablet", "Laptop"]
            device = c1.selectbox("📱 Device Type", dev_types)
            price = c2.select_slider("💵 Price (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10, 15, 20])
            
            if st.form_submit_button("✅ CHECK-IN DEVICE"):
                new_row = {"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Card": card, "Name": name, 
                           "Device": device, "Price": price, "Status": "Charging", "Staff": safe_user}
                cust_df = pd.concat([cust_df, pd.DataFrame([new_row])], ignore_index=True)
                save_data("cust", cust_df)
                st.success(f"Card {card} Checked In!")
                st.rerun()

    st.divider()
    # 2. THE PROFESSIONAL ACTIVE TABLE
st.subheader("📋 Active Queue")

# Filter for items currently in the shop
# This prevents crashes if the file is new or empty
if 'Status' in cust_df.columns:
    active_df = cust_df[cust_df['Status'] == "Charging"]
else:
    active_df = pd.DataFrame()

if active_df.empty:
    st.info("No devices are currently in the shop.")
else:
    # Table Header UI
    h1, h2, h3 = st.columns([1, 3, 2])
    h1.write("**Card**")
    h2.write("**Customer Details**")
    h3.write("**Action**")
    st.markdown("---")

    # Table Rows
    for idx, row in active_df.iterrows():
        r1, r2, r3 = st.columns([1, 3, 2])
        
        # Column 1: Card ID
        r1.warning(f"#{row.get('Card', 'N/A')}")
        
        # Column 2: Customer & Device Info
        r2.markdown(f"**{row.get('Name', 'Unknown')}**")
        r2.caption(f"{row.get('Device', 'Device')} | Le {row.get('Price', '0')}")
        
        # Column 3: Collection Button
        if r3.button("Collected ✅", key=f"col_{idx}", use_container_width=True):
            cust_df.at[idx, 'Status'] = "Collected"
            save_data("cust", cust_df)
            st.rerun()
            
        st.markdown("<hr style='margin:2px; opacity:0.1'>", unsafe_allow_html=True)

    st.subheader("📋 Active Devices (Confirm Collection)")
    
    active_df = cust_df[cust_df['Status'] == "Charging"]
    if not active_df.empty:
        search = st.text_input("🔍 Search Name or Card...")
        if search:
            active_df = active_df[active_df['Name'].str.contains(search, case=False) | active_df['Card'].astype(str).str.contains(search)]
            
        for idx, row in active_df.iterrows():
            with st.container():
                col_det, col_btn = st.columns([3, 1])
                col_det.info(f"**#{row['Card']}** | {row['Name']} | {row['Device']} (Le {row['Price']})")
                if col_btn.button("✅ RETURN", key=f"ret_{idx}"):
                    cust_df.at[idx, 'Status'] = "Collected"
                    save_data("cust", cust_df)
                    st.success("Returned!")
                    st.rerun()
    else:
        st.info("No devices currently charging.")
        
# --- 8. RETAIL SHOP (POS) ---
elif choice == "🛒 Retail Shop":
    st.header("🛒 Retail Shop POS")
    t1, t2 = st.tabs(["💸 Sell Item", "📦 Stock List"])
    
    with t1:
        if not inv_df.empty:
            sell_item = st.selectbox("Select Item", inv_df['Item'].unique())
            curr_stock = inv_df.loc[inv_df['Item'] == sell_item, 'Stock'].values[0]
            curr_price = inv_df.loc[inv_df['Item'] == sell_item, 'Price'].values[0]
            
            st.write(f"**Stock:** {curr_stock} | **Price:** Le {curr_price}")
            
            if st.button("💰 CONFIRM SALE"):
                if curr_stock > 0:
                    idx = inv_df.index[inv_df['Item'] == sell_item][0]
                    inv_df.at[idx, 'Stock'] -= 1
                    save_data("inv", inv_df)
                    st.balloons()
                    st.success(f"Sold {sell_item}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Out of Stock!")
        else:
            st.warning("Inventory is empty. Ask Admin to add items.")

    with t2:
        st.dataframe(inv_df, use_container_width=True)
        if st.session_state.auth == "admin":
            st.markdown("### ➕ Add Stock (Admin)")
            with st.form("add_stock"):
                i_name = st.text_input("Item Name")
                i_price = st.number_input("Selling Price", 0.0)
                i_qty = st.number_input("Quantity", 1)
                if st.form_submit_button("Add to Inventory"):
                    new_item = {"Item": i_name, "Stock": i_qty, "Price": i_price, "Cost": 0.0}
                    inv_df = pd.concat([inv_df, pd.DataFrame([new_item])], ignore_index=True)
                    save_data("inv", inv_df)
                    st.success("Item Added!")
                    st.rerun()

# --- 9. MAINTENANCE ---
elif choice == "🔧 Maintenance":
    st.header("🔧 Maintenance Log")
    with st.form("maint_form"):
        act = st.selectbox("Action", ["Oil Change", "Generator Repair", "Cleaning", "Fuel Purchase"])
        cost = st.number_input("Cost (Le)", 0.0)
        note = st.text_input("Notes")
        if st.form_submit_button("Log Maintenance"):
            m_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Action": act, "Cost": cost, "Note": note}
            maint_df = pd.concat([maint_df, pd.DataFrame([m_row])], ignore_index=True)
            save_data("maint", maint_df)
            st.success("Logged!")
            st.rerun()
    st.dataframe(maint_df)

# --- 10. MASTER CONTROL ---
elif choice == "⚙️ Master Control":
    st.header("🔐 Master Controller")
    st.subheader("👥 User Management")
    st.dataframe(login_df)
    
    with st.form("add_user"):
        nu = st.text_input("New Username").lower().strip()
        np = st.text_input("New Password")
        nr = st.selectbox("Role", ["staff", "admin"])
        if st.form_submit_button("Create User"):
            login_df = pd.concat([login_df, pd.DataFrame([{"role": nr, "user": nu, "pw": np}])], ignore_index=True)
            save_data("login", login_df)
            st.success("User Created!")
            st.rerun()

    st.divider()
    if st.button("♻️ FACTORY RESET APP (Danger)"):
        pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status", "Staff"]).to_csv(DB_FILES["cust"], index=False)
        pd.DataFrame(columns=["Date", "Action", "Cost", "Note"]).to_csv(DB_FILES["maint"], index=False)
        st.error("SYSTEM RESET COMPLETE.")
        time.sleep(2)
        st.rerun()

