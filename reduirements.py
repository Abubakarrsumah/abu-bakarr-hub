import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import urllib.parse
import time

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Abubakarr Enterprise Por", layout="wide", initial_sidebar_state="expanded")

# --- 2. THE ERROR-PROOF DATABASE ENGINE ---
DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "login": "secure_logins.csv",
    "maint": "maint_log.csv"
}

def init_system():
    """Self-healing database: creates files and repairs missing columns automatically."""
    for key, path in DB_FILES.items():
        # Define the Perfect Column Structure
        if key == "cust":
            cols = ["Date", "Card", "Name", "Device", "Price", "Status", "Staff"]
        elif key == "inv":
            cols = ["Item", "Stock", "Price", "Cost", "Category"]
        elif key == "login":
            cols = ["role", "user", "pw"]
        else:
            cols = ["Date", "Action", "Cost", "Note"]

        if not os.path.exists(path) or os.stat(path).st_size == 0:
            # Create fresh file
            df = pd.DataFrame(columns=cols)
            if key == "login": # Add default admin if empty
                df = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"}])
            df.to_csv(path, index=False)
        else:
            # AUTO-REPAIR: Add missing columns to existing files
            df = pd.read_csv(path)
            for col in cols:
                if col not in df.columns:
                    df[col] = 0 if col in ["Price", "Cost", "Stock"] else "N/A"
            df.to_csv(path, index=False)

init_system()

# --- 3. DATA PERSISTENCE LAYER ---
def load_data(key): return pd.read_csv(DB_FILES[key])
def save_data(key, df): df.to_csv(DB_FILES[key], index=False)

# Load into session memory
cust_df = load_data("cust")
inv_df = load_data("inv")
login_df = load_data("login")

# --- 4. SECURE BIOMETRIC-STYLE LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = None
if 'user' not in st.session_state: st.session_state.user = None

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>🏙️ Abubakarr Enterprise Por</h1>", unsafe_allow_html=True)
    st.info("🔐 Restricted Access: Please verify identity.")
    with st.container():
        _, col, _ = st.columns([1, 2, 1])
        with col:
            u = st.text_input("Username").lower().strip()
            p = st.text_input("Password", type="password")
            if st.button("🔓 LOG IN", use_container_width=True):
                match = login_df[(login_df['user'] == u) & (login_df['pw'].astype(str) == p)]
                if not match.empty:
                    st.session_state.auth = match.iloc[0]['role']
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Access Denied")
    st.stop()

# --- 5. AI ASSISTANT & 3-BAG BRAIN ---
st.sidebar.title(f"🚀 {st.session_state.user.upper()} PORTAL")
rev_today = cust_df[cust_df['Date'] == datetime.now().strftime("%Y-%m-%d")]['Price'].sum() if not cust_df.empty else 0
total_rev = cust_df['Price'].sum() if not cust_df.empty else 0

# 🧠 AI KRIO PREDICTOR
st.sidebar.markdown("### 🧠 AI Krio Brain")
if not cust_df.empty:
    busiest_day = pd.to_datetime(cust_df['Date']).dt.day_name().mode()[0]
    st.sidebar.success(f"AI: 'De busiest day na **{busiest_day}**. Prepare staff!'")
else:
    st.sidebar.write("AI: 'I de wait for more data for predict.'")

# 💰 3-BAG SYSTEM
st.sidebar.markdown("---")
st.sidebar.markdown("### 👜 THE 3-BAGS (Wealth Tracker)")
st.sidebar.info(f"👜 Bag 1 (Ops 40%): Le {total_rev * 0.4:,.0f}")
st.sidebar.warning(f"📦 Bag 2 (Stock 30%): Le {total_rev * 0.3:,.0f}")
st.sidebar.success(f"💰 Bag 3 (Wealth 30%): Le {total_rev * 0.3:,.0f}")

menu = ["⚡ Charging Hub", "🛒 Retail Shop", "📊 Business Reports", "⚙️ Admin Controls"]
choice = st.sidebar.radio("Navigate", menu)

if st.sidebar.button("🚪 Shutdown Session"):
    st.session_state.auth = None
    st.rerun()

# --- 6. CHARGING HUB (WITH COLLECTION TRACKING & TABLE) ---
if choice == "⚡ Charging Hub":
    st.header("⚡ Master Charging Registry")
    
    with st.expander("📝 Register New Device Entry", expanded=True):
        with st.form("charge_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            card = c1.selectbox("Card Number", list(range(0, 101)))
            name = c2.text_input("Customer Name")
            device_list = ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank", "Bluetooth Speaker", "Tablet"]
            device = c3.selectbox("Device Type", device_list)
            price = c1.select_slider("Fee (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10])
            
            if st.form_submit_button("✅ SAVE & PRINT RECEIPT"):
                new_entry = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Card": card, "Name": name, 
                                           "Device": device, "Price": price, "Status": "Charging", "Staff": st.session_state.user}])
                cust_df = pd.concat([cust_df, new_entry], ignore_index=True)
                save_data("cust", cust_df)
                st.success(f"Receipt Generated for Card {card}!")
                st.rerun()

    st.subheader("📋 Active Charging Queue")
    # Search Filter
    search = st.text_input("🔍 Search Card or Name")
    display_df = cust_df[cust_df['Status'] == "Charging"]
    if search: display_df = display_df[display_df['Name'].str.contains(search, case=False) | display_df['Card'].astype(str).contains(search)]

    if not display_df.empty:
        for idx, row in display_df.iterrows():
            col_info, col_btn = st.columns([4, 1])
            col_info.warning(f"🎫 **Card {row['Card']}** | {row['Name']} ({row['Device']}) | Le {row['Price']}")
            if col_btn.button("Confirm Collection ✅", key=f"col_{idx}"):
                cust_df.at[idx, 'Status'] = "Collected"
                save_data("cust", cust_df)
                st.rerun()
    else: st.info("No devices are currently in the shop.")

    st.subheader("📊 Full History Table")
    st.dataframe(cust_df, use_container_width=True)

# --- 7. RETAIL SHOP (WITH COST/PROFIT TRACKING) ---
elif choice == "🛒 Retail Shop":
    st.header("🛒 Shop Inventory & Sales")
    t1, t2 = st.tabs(["💰 Sell Item", "📦 Stock Manager"])
    
    with t1:
        if not inv_df.empty:
            sell_item = st.selectbox("Select Product", inv_df['Item'].unique())
            item_data = inv_df[inv_df['Item'] == sell_item].iloc[0]
            st.metric("Price", f"Le {item_data['Price']}", f"Stock: {item_data['Stock']}")
            
            if st.button("Confirm Sale (POS)"):
                if item_data['Stock'] > 0:
                    inv_df.loc[inv_df['Item'] == sell_item, 'Stock'] -= 1
                    save_data("inv", inv_df)
                    st.success("Sale Complete!")
                    st.rerun()
                else: st.error("Insufficient Stock!")
        else: st.info("No items in shop.")

    with t2:
        st.dataframe(inv_df, use_container_width=True)
        if st.session_state.auth == "admin":
            st.markdown("### ➕ Restock (Admin Only)")
            with st.form("stock_form"):
                sc1, sc2 = st.columns(2)
                ni = sc1.text_input("Item Name")
                nc = sc2.number_input("Buying COST (Le)", 0.0) # THE FIELD YOU REQUESTED
                np = sc1.number_input("Selling PRICE (Le)", 0.0)
                nq = sc2.number_input("Quantity", 1)
                if st.form_submit_button("Add to Stock"):
                    new_item = pd.DataFrame([{"Item": ni, "Stock": nq, "Price": np, "Cost": nc}])
                    inv_df = pd.concat([inv_df, new_item], ignore_index=True)
                    save_data("inv", inv_df)
                    st.rerun()

# --- 8. REPORTS & WHATSAPP ---
elif choice == "📊 Business Reports":
    st.title("📊 Financial Intelligence")
    k1, k2, k3 = st.columns(3)
    k1.metric("Today Revenue", f"Le {rev_today}")
    k2.metric("Total Devices", len(cust_df))
    # Simple profit calculation (Sell Price - Cost Price)
    profit = (inv_df['Price'] - inv_df['Cost']).sum() if not inv_df.empty else 0
    k3.metric("Retail Profit Est.", f"Le {profit}")

    st.divider()
    st.subheader("📲 Send WhatsApp Daily Report")
    report_msg = f"*🏪 Abubakarr Enterprise Por Report*\nDate: {datetime.now().strftime('%Y-%m-%d')}\nRev: Le {total_rev}\nWealth Bag: Le {total_rev*0.3}"
    encoded_msg = urllib.parse.quote(report_msg)
    st.link_button("📤 Send Report to Boss", f"https://wa.me/?text={encoded_msg}")

# --- 9. ADMIN MASTER CONTROLS ---
elif choice == "⚙️ Admin Controls":
    if st.session_state.auth == "admin":
        st.header("🔐 Master Security Console")
        
        # User Management
        st.subheader("👥 Manage Staff Accounts")
        st.table(login_df[['user', 'role']])
        with st.expander("Add New Staff"):
            nu = st.text_input("New Username")
            np = st.text_input("New Password")
            if st.button("Create Account"):
                login_df = pd.concat([login_df, pd.DataFrame([{"role": "staff", "user": nu, "pw": np}])], ignore_index=True)
                save_data("login", login_df)
                st.rerun()
        
        # Reset System
        st.divider()
        if st.button("🧨 WIPE ALL BUSINESS HISTORY"):
            pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status", "Staff"]).to_csv(DB_FILES["cust"], index=False)
            st.error("System Cleared Successfully.")
            time.sleep(1)
            st.rerun()
    else:
        st.error("⛔ Access Denied: Admin Level Required.")
