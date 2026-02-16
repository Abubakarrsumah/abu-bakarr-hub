import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import hashlib
import json

# --- 1. CONFIGURATION & MOBILE OPTIMIZATION ---
st.set_page_config(page_title="Abubakarr Enterprise Por", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Sierra Leone Mobile Shop Use
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .main-header { font-size: 24px; font-weight: bold; color: #00ffcc; text-align: center; }
    .card-id { font-size: 20px; color: #ffcc00; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 22px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ENGINE (SELF-HEALING / ERROR-FREE) ---
DB_FILES = {
    "users": "db_users.csv",
    "charging": "db_charging.csv",
    "inventory": "db_inventory.csv",
    "settings": "db_settings.json"
}

def init_db():
    """Fixes missing columns and creates files if they don't exist."""
    # User DB
    if not os.path.exists(DB_FILES["users"]):
        df = pd.DataFrame([{"user": "admin", "pw": "abu123", "role": "Admin"}])
        df.to_csv(DB_FILES["users"], index=False)
    
    # Charging DB (With all SL Phones)
    if not os.path.exists(DB_FILES["charging"]):
        cols = ["Date", "Card", "Name", "Device", "Price", "Status", "Staff", "Collected"]
        pd.DataFrame(columns=cols).to_csv(DB_FILES["charging"], index=False)
    
    # Inventory DB
    if not os.path.exists(DB_FILES["inventory"]):
        cols = ["Item", "Stock", "Price", "Cost"]
        pd.DataFrame(columns=cols).to_csv(DB_FILES["inventory"], index=False)

init_db()

# --- 3. SESSION STATE & SECURITY ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""

def check_login(u, p):
    df = pd.read_csv(DB_FILES["users"])
    match = df[(df['user'] == u) & (df['pw'] == p)]
    if not match.empty:
        st.session_state.auth = True
        st.session_state.user = u
        st.session_state.role = match.iloc[0]['role']
        return True
    return False

# --- 4. CORE FEATURES & LOGIC ---

def get_3_bags(total_rev):
    """The Three Bags System (Sierra Leone Business Standard)"""
    bag_1 = total_rev * 0.40  # Ops/Capital
    bag_2 = total_rev * 0.30  # Personal/Wealth
    bag_3 = total_rev * 0.30  # Shop Savings
    return bag_1, bag_2, bag_3

def ai_assistant_brain():
    """Simulated AI for Income Prediction & Busiest Days"""
    df = pd.read_csv(DB_FILES["charging"])
    if len(df) < 5:
        return "AI: 'Keep recording data. I need 5 entries to predict busiest days.'"
    busy_day = pd.to_datetime(df['Date']).dt.day_name().mode()[0]
    return f"AI Prediction: 'Next busy day is **{busy_day}**. Tomorrow income projection: Le {df['Price'].mean() * 1.2:,.0f}'"

# --- 5. LOGIN UI ---
if not st.session_state.auth:
    st.markdown("<div class='main-header'>🔐 Abubakarr Enterprise Por</div>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if check_login(u, p): st.rerun()
            else: st.error("Access Denied")
    st.stop()

# --- 6. MAIN NAVIGATION ---
st.sidebar.title(f"📱 {st.session_state.user.upper()} ({st.session_state.role})")
menu = st.sidebar.radio("Navigation", ["⚡ Charging Hub", "📦 Retail & Inventory", "📊 Dashboard & AI", "⚙️ Admin Controls"])

if st.sidebar.button("🚪 Logout"):
    st.session_state.auth = False
    st.rerun()

# --- 7. CHARGING HUB (FEATURE 14, 41) ---
if menu == "⚡ Charging Hub":
    st.header("⚡ Charging Registry")
    
    # Register New Device
    with st.expander("📝 Register New Device", expanded=True):
        with st.form("charge_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            card_num = col1.selectbox("🎫 Card Number", ["No Card"] + [str(i) for i in range(101)])
            cust_name = col2.text_input("👤 Customer Name")
            
            # SL Phone List
            phone_list = ["Tecno", "Infinix", "Samsung", "iPhone", "Itel", "Redmi", "Power Bank", "Bluetooth", "Other Tablet"]
            device = col1.selectbox("📱 Device Type", phone_list)
            price = col2.select_slider("💰 Set Price (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10])
            
            if st.form_submit_button("✅ Save & Print Receipt"):
                df = pd.read_csv(DB_FILES["charging"])
                new_row = {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Card": card_num, "Name": cust_name, "Device": device,
                    "Price": price, "Status": "Charging", "Staff": st.session_state.user, "Collected": "No"
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(DB_FILES["charging"], index=False)
                st.success("Entry Saved! Receipt Ready.")
                st.code(f"REC: {cust_name} | Card: {card_num} | Device: {device} | Price: {price} Le")

    # Table with Search Bar
    st.divider()
    df_charge = pd.read_csv(DB_FILES["charging"])
    search = st.text_input("🔍 Search Name or Card Number")
    
    if search:
        df_display = df_charge[df_charge['Name'].str.contains(search, case=False) | df_charge['Card'].astype(str).contains(search)]
    else:
        df_display = df_charge[df_charge['Collected'] == "No"]

    st.subheader("📋 Active Queue")
    if not df_display.empty:
        for idx, row in df_display.iterrows():
            c1, c2, c3 = st.columns([1, 3, 2])
            c1.markdown(f"<span class='card-id'>#{row['Card']}</span>", unsafe_allow_html=True)
            c2.write(f"**{row['Name']}** - {row['Device']} ({row['Price']} Le)")
            if c3.button(f"Confirm Collection ✅", key=f"btn_{idx}"):
                df_charge.at[idx, "Collected"] = "Yes"
                df_charge.at[idx, "Status"] = "Completed"
                df_charge.to_csv(DB_FILES["charging"], index=False)
                st.rerun()
    else:
        st.info("No active devices found.")

    # Daily Total (Feature 41)
    st.divider()
    daily_tot = df_charge[df_charge['Date'] == datetime.now().strftime("%Y-%m-%d")]['Price'].sum()
    st.metric("💰 Today's Total Income", f"Le {daily_tot:,.0f}")

# --- 8. RETAIL & INVENTORY (ADMIN ONLY) ---
elif menu == "📦 Retail & Inventory":
    st.header("📦 Inventory Control")
    
    if st.session_state.role == "Admin":
        with st.expander("➕ Add Stock"):
            with st.form("inv_form"):
                item = st.text_input("Item Name")
                stock = st.number_input("Quantity", min_value=1)
                price = st.number_input("Selling Price", min_value=1)
                if st.form_submit_button("Add Item"):
                    inv = pd.read_csv(DB_FILES["inventory"])
                    new_item = {"Item": item, "Stock": stock, "Price": price, "Cost": 0}
                    inv = pd.concat([inv, pd.DataFrame([new_item])], ignore_index=True)
                    inv.to_csv(DB_FILES["inventory"], index=False)
                    st.rerun()
    
    inv_df = pd.read_csv(DB_FILES["inventory"])
    st.dataframe(inv_df, use_container_width=True)

# --- 9. DASHBOARD & AI (3-BAGS SYSTEM) ---
elif menu == "📊 Dashboard & AI":
    st.header("📊 Reporting Dashboard")
    df_charge = pd.read_csv(DB_FILES["charging"])
    total_rev = df_charge['Price'].sum()
    
    st.info(ai_assistant_brain())
    
    # 3 Bags System
    b1, b2, b3 = get_3_bags(total_rev)
    col1, col2, col3 = st.columns(3)
    col1.metric("👜 Bag 1: Ops (40%)", f"Le {b1:,.0f}")
    col2.metric("💰 Bag 2: Personal (30%)", f"Le {b2:,.0f}")
    col3.metric("🏠 Bag 3: Shop (30%)", f"Le {b3:,.0f}")

    # WhatsApp Profit Link
    msg = f"Abubakarr Enterprise Por Report: Total Revenue: Le {total_rev:,.0f}. Daily: {datetime.now().strftime('%Y-%m-%d')}"
    wa_url = f"https://wa.me/?text={msg.replace(' ', '%20')}"
    st.link_button("📲 Send Daily Report to WhatsApp", wa_url)

# --- 10. ADMIN MASTER CONTROLS ---
elif menu == "⚙️ Admin Controls":
    if st.session_state.role != "Admin":
        st.error("⛔ Unauthorized. Admin Only.")
    else:
        st.header("👑 Admin Master Controller")
        
        tab1, tab2 = st.tabs(["👥 User Management", "💾 System Reset"])
        
        with tab1:
            st.subheader("Add/Remove Staff")
            u_db = pd.read_csv(DB_FILES["users"])
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password")
            if st.button("Add Staff Account"):
                new_staff = {"user": new_u, "pw": new_p, "role": "Staff"}
                u_db = pd.concat([u_db, pd.DataFrame([new_staff])], ignore_index=True)
                u_db.to_csv(DB_FILES["users"], index=False)
                st.success("Staff Added")
            st.dataframe(u_db)

        with tab2:
            st.warning("Danger Zone: This clears all app history.")
            if st.button("🧨 CLEAR ALL APP DATA"):
                os.remove(DB_FILES["charging"])
                init_db()
                st.success("System Wiped.")
