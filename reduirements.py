import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import random
import json

# --- 1. PAGE CONFIG & THEME ---
st.set_page_config(page_title="Abubakarr Enterprise Pro", page_icon="⚡", layout="wide")

# Professional UI Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 10px; }
    .krio-msg { color: #00ffcc; font-style: italic; }
    .card-id { font-size: 24px; font-weight: bold; color: #ffcc00; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SELF-HEALING DATABASE ENGINE ---
DB = {
    "users": "db_users.csv",
    "charging": "db_charging.csv",
    "inventory": "db_inventory.csv",
    "maintenance": "db_maint.csv",
    "meta": "db_metadata.json"
}

def init_db():
    # User DB
    if not os.path.exists(DB["users"]):
        pd.DataFrame([{"user": "admin", "pw": "abu123", "role": "Admin"}]).to_csv(DB["users"], index=False)
    
    # Charging DB
    if not os.path.exists(DB["charging"]):
        cols = ["Date", "Card", "Name", "Device", "Price", "Status", "Staff", "Collected", "Phone"]
        pd.DataFrame(columns=cols).to_csv(DB["charging"], index=False)
    
    # Inventory DB
    if not os.path.exists(DB["inventory"]):
        pd.DataFrame(columns=["Item", "Stock", "Price", "Cost"]).to_csv(DB["inventory"], index=False)

    # Maintenance DB (Oil/Fuel)
    if not os.path.exists(DB["maintenance"]):
        pd.DataFrame(columns=["Date", "Type", "Amount", "Cost", "Note"]).to_csv(DB["maintenance"], index=False)

init_db()

# --- 3. CORE ANALYTICS FUNCTIONS ---
def load_db(key): return pd.read_csv(DB[key])
def save_db(key, df): df.to_csv(DB[key], index=False)

def get_3_bags():
    df = load_db("charging")
    today = datetime.now().strftime("%Y-%m-%d")
    total = df[df['Date'] == today]['Price'].sum()
    return {"total": total, "ops": total*0.4, "stock": total*0.3, "profit": total*0.3}

# --- 4. SECURE AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user' not in st.session_state: st.session_state.user = ""
if 'role' not in st.session_state: st.session_state.role = ""

def login():
    st.title("🔐 Abubakarr Ent. Pro")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("🚀 Enter Shop"):
        users = load_db("users")
        match = users[(users['user'] == u) & (users['pw'] == p)]
        if not match.empty:
            st.session_state.auth = True
            st.session_state.user = u
            st.session_state.role = match.iloc[0]['role']
            st.rerun()
        else:
            st.error("Access Denied")
    st.info("💡 Tip: Use Biometric Bypass (Admin Hardware Required)")

# --- 5. MAIN APPLICATION LOGIC ---
if not st.session_state.auth:
    login()
else:
    # --- SIDEBAR: AI & DASHBOARD ---
    st.sidebar.title(f"👤 {st.session_state.user.upper()}")
    st.sidebar.markdown(f"**Role:** {st.session_state.role}")
    
    # 3-Bags Widget
    bags = get_3_bags()
    st.sidebar.divider()
    st.sidebar.subheader("👜 The 3-Bags Wallet")
    st.sidebar.write(f"💼 Ops (40%): **Le {bags['ops']:,.1f}**")
    st.sidebar.write(f"📦 Stock (30%): **Le {bags['stock']:,.1f}**")
    st.sidebar.write(f"💰 Profit (30%): **Le {bags['profit']:,.1f}**")
    
    st.sidebar.divider()
    menu = st.sidebar.radio("Navigate", ["⚡ Charging Hub", "🛒 Inventory & POS", "📊 AI Dashboard", "🛠️ Maintenance", "⚙️ Admin Control"])
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.auth = False
        st.rerun()

    # --- A. CHARGING HUB ---
    if menu == "⚡ Charging Hub":
        st.header("🏪 Charging Registry")
        
        # 1. Entry Form
        with st.expander("➕ New Device Check-in", expanded=True):
            with st.form("charge_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                card = col1.selectbox("🎫 Card #", ["NONE"] + [str(i) for i in range(1, 101)])
                name = col2.text_input("👤 Customer Name")
                
                phones = ["Tecno", "Infinix", "Samsung", "iPhone", "Itel", "Redmi", "Power Bank", "Speaker", "Other"]
                device = col1.selectbox("📱 Device Type", phones)
                price = col2.select_slider("💵 Fee (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10])
                phone_num = col2.text_input("📞 Phone # (WhatsApp Bot)")
                
                if st.form_submit_button("✅ SAVE & PRINT"):
                    df = load_db("charging")
                    new_entry = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Card": card, "Name": name, "Device": device,
                        "Price": price, "Status": "Charging", "Staff": st.session_state.user,
                        "Collected": "No", "Phone": phone_num
                    }])
                    save_db("charging", pd.concat([df, new_entry]))
                    st.success("Entry Registered!")
                    st.code(f"REC: {name} | Card: {card} | Le {price}", language="text")

        # 2. Search & Table
        st.divider()
        search = st.text_input("🔍 Search Card # or Name...")
        df_c = load_db("charging")
        active_df = df_c[df_c['Collected'] == "No"]
        
        if search:
            active_df = active_df[active_df['Name'].str.contains(search, case=False) | active_df['Card'].astype(str).contains(search)]

        st.subheader("📋 Active Queue")
        if active_df.empty:
            st.info("No phones are currently charging.")
        else:
            for idx, row in active_df.iterrows():
                c1, c2, c3 = st.columns([1, 3, 2])
                c1.markdown(f"<div class='card-id'>#{row['Card']}</div>", unsafe_allow_html=True)
                c2.write(f"**{row['Name']}** | {row['Device']} | Le {row['Price']}")
                
                # Collection & Receipt Actions
                act1, act2 = c3.columns(2)
                if act1.button("✅ Collect", key=f"col_{idx}"):
                    df_c.at[idx, 'Collected'] = "Yes"
                    save_db("charging", df_c)
                    st.rerun()
                if act2.button("🧾 Print", key=f"prt_{idx}"):
                    st.toast("Generating Receipt...")

        st.markdown(f"### 💵 Today's Daily Total: Le {bags['total']:,.0f}")

    # --- B. INVENTORY & POS ---
    elif menu == "🛒 Inventory & POS":
        st.header("📦 Inventory Control")
        inv = load_db("inventory")
        
        if st.session_state.role == "Admin":
            with st.expander("Add New Stock"):
                with st.form("inv_form"):
                    i_name = st.text_input("Item Name")
                    i_qty = st.number_input("Quantity", 1)
                    i_price = st.number_input("Selling Price", 1)
                    if st.form_submit_button("Update Stock"):
                        new_inv = pd.concat([inv, pd.DataFrame([{"Item": i_name, "Stock": i_qty, "Price": i_price}])])
                        save_db("inventory", new_inv)
                        st.rerun()
        
        st.dataframe(inv, use_container_width=True)

    # --- C. AI DASHBOARD ---
    elif menu == "📊 AI Dashboard":
        st.header("🧠 AI Business Brain")
        
        c1, c2 = st.columns(2)
        c1.metric("Predicted Income Tomorrow", f"Le {bags['total'] * 1.15:,.0f}")
        c2.metric("Busiest Day", "Saturday")
        
        st.markdown("<p class='krio-msg'>AI Says: 'Boss, prepare fuel for tomorrow. Saturday go busy and NEPA might go off.'</p>", unsafe_allow_html=True)
        
        st.divider()
        if st.button("📤 Send Daily Report to WhatsApp"):
            msg = f"Abubakarr Pro Report: Total Le {bags['total']}. Profit Le {bags['profit']}."
            st.link_button("Send to Boss", f"https://wa.me/?text={msg}")

    # --- D. MAINTENANCE ---
    elif menu == "🛠️ Maintenance":
        st.header("🛠️ Machine Maintenance (Oil/Fuel)")
        m_df = load_db("maintenance")
        
        with st.form("maint_form"):
            m_type = st.selectbox("Type", ["Fuel", "Engine Oil", "Filter", "Generator Repair"])
            m_amt = st.number_input("Amount (Le)", 1)
            m_note = st.text_area("Notes")
            if st.form_submit_button("Record Maintenance"):
                new_m = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Type": m_type, "Amount": m_amt, "Cost": m_amt, "Note": m_note}])
                save_db("maintenance", pd.concat([m_df, new_m]))
                st.success("Maintenance logged!")
        
        st.dataframe(m_df, use_container_width=True)

    # --- E. ADMIN CONTROL ---
    elif menu == "⚙️ Admin Control":
        if st.session_state.role != "Admin":
            st.error("⛔ Access Denied.")
        else:
            st.header("⚙️ Master Controller")
            
            # User Management
            st.subheader("👥 User Management")
            u_df = load_db("users")
            st.dataframe(u_df)
            
            # Reset Data
            if st.button("🗑️ Reset All App History"):
                os.remove(DB["charging"])
                init_db()
                st.success("History Wiped!")
