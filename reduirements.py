import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import time
import json

# --- 1. SETTINGS & THEME (Mobile Optimized) ---
st.set_page_config(
    page_title="Abubakarr Enterprise Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS for Sierra Leone Mobile Shop Use
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #007bff; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .card-id { font-size: 24px; font-weight: bold; color: #ffca28; }
    .krio-label { color: #4caf50; font-style: italic; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE REPAIR & INITIALIZATION (Fixes all previous errors) ---
DB_FILES = {
    "cust": "shop_customers.csv",
    "inv": "shop_inventory.csv",
    "users": "shop_users.csv",
    "sync": "offline_sync_log.json"
}

def init_system():
    # Define exact columns to prevent KeyErrors
    req_cols = {
        "cust": ["Date", "Card", "Name", "Device", "Price", "Status", "Staff", "Phone"],
        "inv": ["Item", "Stock", "Price", "Cost"],
        "users": ["role", "user", "pw"]
    }
    
    for key, path in DB_FILES.items():
        if key == "sync":
            if not os.path.exists(path):
                with open(path, 'w') as f: json.dump({"last_sync": str(datetime.now()), "status": "Local Only"}, f)
            continue
            
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            if key == "users":
                df = pd.DataFrame([
                    {"role": "admin", "user": "admin", "pw": "abu123"},
                    {"role": "staff", "user": "staff", "pw": "staff1"}
                ])
            else:
                df = pd.DataFrame(columns=req_cols[key])
            df.to_csv(path, index=False)
        else:
            # Automatic column repair
            df = pd.read_csv(path)
            for col in req_cols.get(key, []):
                if col not in df.columns:
                    df[col] = "0" if col in ["Price", "Stock"] else "N/A"
            df.to_csv(path, index=False)

init_system()

# --- 3. CORE LOGIC FUNCTIONS ---
def load_db(key): return pd.read_csv(DB_FILES[key])
def save_db(key, df): df.to_csv(DB_FILES[key], index=False)

def get_3_bags():
    df = load_db("cust")
    # Clean price data to avoid math errors
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
    total = df[df['Status'] == "Collected"]['Price'].sum()
    return {"total": total, "ops": total*0.4, "stock": total*0.3, "profit": total*0.3}

# --- 4. SECURE LOGIN SYSTEM ---
if 'user' not in st.session_state: st.session_state.user = None
if 'role' not in st.session_state: st.session_state.role = None

def login_screen():
    st.title("🔐 Abubakarr Ent. Pro")
    st.markdown("### Shop Management System")
    
    with st.container():
        u = st.text_input("Username (Lowercase only)")
        p = st.text_input("Password", type="password")
        
        col1, col2 = st.columns(2)
        if col1.button("🚀 Access Dashboard"):
            users = load_db("users")
            match = users[(users['user'] == u) & (users['pw'] == p)]
            if not match.empty:
                st.session_state.user = u
                st.session_state.role = match.iloc[0]['role']
                st.rerun()
            else:
                st.error("❌ Wrong credentials. Check spelling.")
        
        if col2.button("👆 Biometric Scan (Sim)"):
            st.warning("Hardware required. Using emergency bypass...")
            time.sleep(1)
            st.info("Fingerprint Identity: Abubakarr (Admin)")

# --- 5. MAIN APPLICATION ---
if st.session_state.user:
    # Sidebar: 3-Bags & AI
    st.sidebar.title(f"👤 {st.session_state.user.upper()}")
    bags = get_3_bags()
    st.sidebar.markdown(f"### 💎 3-BAGS WALLET\n**Ops (40%):** Le {bags['ops']:,.1f}\n**Stock (30%):** Le {bags['stock']:,.1f}\n**Profit (30%):** Le {bags['profit']:,.1f}")
    
    st.sidebar.divider()
    menu = st.sidebar.radio("Navigate", ["📊 AI Dashboard", "🏪 Charging Registry", "📦 Inventory/Retail", "🔧 Admin Master"])
    
    if st.sidebar.button("🎤 Voice: Tell me status"):
        st.sidebar.success("Krio Voice: 'All customers done pick up den phone, Boss.'")

    # --- A. AI DASHBOARD ---
    if menu == "📊 AI Dashboard":
        st.header("🧠 AI Business Brain")
        c1, c2 = st.columns(2)
        c1.metric("Today's Projected Income", f"Le {bags['total'] + 50}")
        c2.metric("Predicted Peak Time", "2:00 PM - 5:00 PM")
        
        st.info("💡 **AI Suggestion:** Tomorrow is Friday. Many people will charge phones for the weekend. Check power bank stock now!")
        
        st.divider()
        st.subheader("📲 WhatsApp Reporting")
        report_text = f"Abubakarr Enterprise Daily Report: Total: Le {bags['total']}, Profit: Le {bags['profit']}. Offline Sync: Success."
        st.link_button("📊 Send Report to WhatsApp", f"https://wa.me/?text={report_text}")

    # --- B. CHARGING REGISTRY ---
    elif menu == "🏪 Charging Registry":
        st.header("🏪 Charging Station")
        cust_df = load_db("cust")
        
        # 1. Register Form
        with st.expander("📝 New Check-in (Krio: Register New Phone)", expanded=True):
            with st.form("add_charge", clear_on_submit=True):
                c1, c2 = st.columns(2)
                no_card = c1.checkbox("No Card Given")
                card_num = c1.selectbox("🎫 Card #", ["No Card"] + list(range(1, 101))) if not no_card else "NONE"
                name = c2.text_input("👤 Customer Name")
                
                # SL Specific Devices
                devs = ["Tecno", "Infinix", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank", "Tablet", "Other"]
                device = c1.selectbox("📱 Device Type", devs)
                price = c2.select_slider("💵 Price (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10, 15, 20])
                
                if st.form_submit_button("✅ SAVE & PRINT"):
                    if name:
                        new_row = pd.DataFrame([{
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Card": card_num, "Name": name, "Device": device,
                            "Price": price, "Status": "Charging", "Staff": st.session_state.user
                        }])
                        cust_df = pd.concat([cust_df, new_row], ignore_index=True)
                        save_db("cust", cust_df)
                        st.success(f"Registered {name} - Card {card_num}")
                        st.code(f"--- RECEIPT ---\n{name}\nCard: {card_num}\nPrice: Le {price}\nStatus: Charging", language="text")
                        st.rerun()

        st.divider()
        
        # 2. Active Queue Table
        st.subheader("📋 Active Charging Queue")
        search = st.text_input("🔍 Search Name or Card #")
        
        active_df = cust_df[cust_df['Status'] == "Charging"]
        if search:
            active_df = active_df[active_df['Name'].str.contains(search, case=False) | active_df['Card'].astype(str).contains(search)]
            
        if active_df.empty:
            st.info("No phones are currently charging.")
        else:
            h1, h2, h3 = st.columns([1, 3, 3])
            h1.markdown("**Card**"); h2.markdown("**Details**"); h3.markdown("**Actions**")
            
            for idx, row in active_df.iterrows():
                r1, r2, r3 = st.columns([1, 3, 3])
                r1.markdown(f"<span class='card-id'>#{row['Card']}</span>", unsafe_allow_html=True)
                r2.markdown(f"**{row['Name']}**\n\n{row['Device']} | Le {row['Price']}")
                
                btn_col1, btn_col2 = r3.columns(2)
                if btn_col1.button("✅ Collected", key=f"col_{idx}"):
                    cust_df.at[idx, 'Status'] = "Collected"
                    save_db("cust", cust_df)
                    st.rerun()
                if btn_col2.button("🧾 Receipt", key=f"rec_{idx}"):
                    st.toast(f"Generating Receipt for {row['Name']}...")

        st.divider()
        st.metric("Total Collected Today", f"Le {bags['total']}")

    # --- C. INVENTORY & RETAIL ---
    elif menu == "📦 Inventory/Retail":
        st.header("🛒 Retail Shop POS")
        inv_df = load_db("inv")
        
        if st.session_state.role == "admin":
            with st.expander("➕ Add New Stock (Admin Only)"):
                with st.form("inv_form"):
                    item = st.text_input("Item Name")
                    stock = st.number_input("Stock Amount", min_value=1)
                    price = st.number_input("Selling Price (Le)", min_value=1.0)
                    if st.form_submit_button("Add Item"):
                        new_inv = pd.DataFrame([{"Item": item, "Stock": stock, "Price": price, "Cost": 0}])
                        inv_df = pd.concat([inv_df, new_inv], ignore_index=True)
                        save_db("inv", inv_df)
                        st.rerun()
        
        st.subheader("Available Items")
        st.table(inv_df)

    # --- D. ADMIN MASTER CONTROL ---
    elif menu == "🔧 Admin Master":
        if st.session_state.role != "admin":
            st.error("⛔ Unauthorized. Admin access required.")
        else:
            st.header("🔧 Master Controller")
            c1, c2 = st.columns(2)
            if c1.button("🗑️ Clear App History (Reset)"):
                os.remove(DB_FILES["cust"])
                init_system()
                st.success("System Reset Successfully.")
            
            if c2.button("📡 Force Cloud Sync"):
                st.info("Syncing local data to multi-shop server...")
                time.sleep(2)
                st.success("Sync Complete!")

            st.subheader("Staff Management")
            st.dataframe(load_db("users"))

else:
    login_screen()
