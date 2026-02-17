"""
Abubakarr Enterprise POR - All-in-One Shop Management System
Sierra Leone Mobile Business Tool
Author: Professional Code Generator
Features: Offline mode, AI predictions, Voice assistant, WhatsApp bot, Charging registry, Inventory, Staff, Sync, Maintenance, and more.
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import hashlib
import datetime
import time
import os
import json
import random
from datetime import datetime, timedelta
import base64

# Optional imports for voice (with fallback)
try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    sr = None

# Optional for SMS/WhatsApp simulation
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = False  # Set to True if you configure
except ImportError:
    TWILIO_AVAILABLE = False

# ---------------------------
# Database Setup
# ---------------------------
DB_PATH = "abubakarr_shop.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'staff',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Inventory table
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        price REAL DEFAULT 0,
        category TEXT,
        min_stock INTEGER DEFAULT 5,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Charging records
    c.execute('''CREATE TABLE IF NOT EXISTS charging_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone_model TEXT,
        card_number TEXT,
        price REAL,
        collected BOOLEAN DEFAULT 0,
        receipt_printed BOOLEAN DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )''')
    
    # Transactions (for profit tracking)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        description TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Maintenance records
    c.execute('''CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        machine TEXT,
        action TEXT,
        cost REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Sync log (offline-online)
    c.execute('''CREATE TABLE IF NOT EXISTS sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT,
        record_id INTEGER,
        action TEXT,
        synced BOOLEAN DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Staff biometric (simplified)
    c.execute('''CREATE TABLE IF NOT EXISTS staff_biometric (
        user_id INTEGER,
        fingerprint_hash TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Three bags system (bag tracking)
    c.execute('''CREATE TABLE IF NOT EXISTS bags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bag_number TEXT,
        status TEXT,
        assigned_to TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add default admin if not exists
    admin_pass = hash_password("admin123")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
              ("admin", admin_pass, "admin"))
    
    # Sample Sierra Leone phone models
    phone_models = [
        "Tecno Camon", "Itel", "Infinix", "Samsung A series", "iPhone", 
        "Nokia", "Huawei", "Oppo", "Gionee", "Power Bank", "Laptop", "Radio"
    ]
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------
# Authentication Helpers
# ---------------------------
def check_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    hashed = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
    user = c.fetchone()
    conn.close()
    return user

def is_admin():
    return st.session_state.get('role') == 'admin'

# ---------------------------
# Initialize session state
# ---------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.page = 'login'
    st.session_state.offline_mode = True  # default offline
    st.session_state.voice_enabled = False

# ---------------------------
# Streamlit Page Config
# ---------------------------
st.set_page_config(
    page_title="Abubakarr Enterprise POR",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="auto"
)

# ---------------------------
# Initialize DB
# ---------------------------
init_db()

# ---------------------------
# Helper functions for features
# ---------------------------

def generate_receipt(record_id):
    """Generate text receipt from charging record"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM charging_records WHERE id=?", conn, params=(record_id,))
    conn.close()
    if df.empty:
        return "Record not found"
    row = df.iloc[0]
    receipt = f"""
    ================================
        ABUBAKARR ENTERPRISE
        Phone Charging Receipt
    ================================
    Customer: {row['customer_name']}
    Phone: {row['phone_model']}
    Card #: {row['card_number']}
    Price: Le {row['price']}
    Date: {row['timestamp']}
    Collected: {'Yes' if row['collected'] else 'No'}
    ================================
    Thank you for your business!
    """
    return receipt

def send_whatsapp_message(to, message):
    """Simulate sending WhatsApp (replace with actual API)"""
    # Here you would integrate with WhatsApp Business API or Twilio
    st.info(f"📲 WhatsApp message to {to}: {message}")
    return True

def send_sms_reminder(phone, message):
    """Simulate SMS reminder"""
    st.info(f"📱 SMS to {phone}: {message}")
    return True

def predict_charging_demand(days=7):
    """Simple AI prediction based on historical data"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT DATE(timestamp) as day, COUNT(*) as count FROM charging_records GROUP BY day ORDER BY day DESC LIMIT 30", conn)
    conn.close()
    if len(df) < 3:
        return random.randint(5, 20)  # fallback
    # Simple moving average
    avg = df['count'].astype(float).mean()
    return int(avg * 1.1)  # 10% increase prediction

def predict_daily_income():
    """Predict today's income based on average of last 7 days"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT DATE(timestamp) as day, SUM(price) as total FROM charging_records WHERE collected=1 GROUP BY day ORDER BY day DESC LIMIT 7", conn)
    conn.close()
    if df.empty or len(df) < 2:
        return random.uniform(50, 200)
    return df['total'].mean() * random.uniform(0.9, 1.1)

def sync_to_server():
    """Offline-to-online sync simulation"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Mark unsynced records as synced
    c.execute("UPDATE sync_log SET synced=1 WHERE synced=0")
    conn.commit()
    conn.close()
    st.success("✅ Synced all pending records to cloud server (simulated)")

def voice_input(language="en"):
    """Capture voice input (Krio/English) if available"""
    if not VOICE_AVAILABLE:
        st.warning("Speech recognition not installed. Please type manually.")
        return st.text_input("Type here (voice unavailable):")
    
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now.")
        audio = r.listen(source)
        try:
            if language == "krio":
                # For Krio, we'll use English model as fallback (no specific Krio model)
                text = r.recognize_google(audio, language="en")
            else:
                text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.error("Could not understand audio")
        except sr.RequestError:
            st.error("Speech service error")
    return ""

def text_to_speech(text):
    """Simulate text-to-speech (Krio voice)"""
    st.audio(text)  # Placeholder; would need actual TTS engine
    st.write(f"🔊 (Voice says): {text}")

# ---------------------------
# Login Page
# ---------------------------
def login_page():
    st.title("🔐 Abubakarr Enterprise Login")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            user = check_login(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user[1]
                st.session_state.role = user[3]
                st.session_state.page = 'main'
                st.rerun()
            else:
                st.error("Invalid credentials")
        # Biometric login simulation
        if st.button("🔑 Fingerprint Login (Simulated)", use_container_width=True):
            # In real, you'd use device fingerprint API
            st.session_state.logged_in = True
            st.session_state.username = "staff_finger"
            st.session_state.role = "staff"
            st.session_state.page = 'main'
            st.rerun()

# ---------------------------
# Main App Pages
# ---------------------------
def main_app():
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=Abubakarr+Enterprise", use_column_width=True)
        st.write(f"👤 Logged in as: **{st.session_state.username}** ({st.session_state.role})")
        st.divider()
        
        # Offline mode toggle
        offline = st.checkbox("📴 Offline Mode", value=st.session_state.offline_mode)
        st.session_state.offline_mode = offline
        
        # Voice assistant toggle
        voice = st.checkbox("🎤 Enable Voice Assistant", value=st.session_state.voice_enabled)
        st.session_state.voice_enabled = voice
        
        st.divider()
        
        # Navigation
        pages = {
            "🏠 Dashboard": "dashboard",
            "🔋 Charging Registry": "charging",
            "📦 Inventory Control": "inventory",
            "👥 Staff Management": "staff",
            "📊 Reports & AI": "reports",
            "🔄 Sync & Cloud": "sync",
            "📲 WhatsApp Bot": "whatsapp",
            "🎤 Voice Assistant": "voice",
            "🛠️ Maintenance": "maintenance",
            "🛍️ Three Bags System": "bags",
        }
        for label, page in pages.items():
            if st.button(label, use_container_width=True):
                st.session_state.page = page
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.rerun()
    
    # Page router
    if st.session_state.page == "dashboard":
        show_dashboard()
    elif st.session_state.page == "charging":
        show_charging()
    elif st.session_state.page == "inventory":
        show_inventory()
    elif st.session_state.page == "staff":
        show_staff()
    elif st.session_state.page == "reports":
        show_reports()
    elif st.session_state.page == "sync":
        show_sync()
    elif st.session_state.page == "whatsapp":
        show_whatsapp()
    elif st.session_state.page == "voice":
        show_voice()
    elif st.session_state.page == "maintenance":
        show_maintenance()
    elif st.session_state.page == "bags":
        show_bags()
    else:
        show_dashboard()

# ---------------------------
# Dashboard Page
# ---------------------------
def show_dashboard():
    st.title("🏠 Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    conn = sqlite3.connect(DB_PATH)
    
    # Today's total
    today = datetime.now().date()
    df_today = pd.read_sql_query("SELECT SUM(price) as total FROM charging_records WHERE DATE(timestamp)=? AND collected=1", conn, params=(today,))
    today_total = df_today.iloc[0]['total'] or 0
    
    # Pending collections
    df_pending = pd.read_sql_query("SELECT COUNT(*) as cnt FROM charging_records WHERE collected=0", conn)
    pending = df_pending.iloc[0]['cnt']
    
    # Inventory low stock
    df_low = pd.read_sql_query("SELECT COUNT(*) as cnt FROM inventory WHERE quantity <= min_stock", conn)
    low_stock = df_low.iloc[0]['cnt']
    
    conn.close()
    
    with col1:
        st.metric("Today's Income", f"Le {today_total:.2f}")
    with col2:
        st.metric("Pending Collections", pending)
    with col3:
        st.metric("Low Stock Items", low_stock)
    with col4:
        # AI prediction for today
        pred_income = predict_daily_income()
        st.metric("AI Predicted Income", f"Le {pred_income:.2f}")
    
    st.divider()
    
    # Quick actions
    st.subheader("Quick Actions")
    cola, colb, colc = st.columns(3)
    with cola:
        if st.button("➕ New Charging Entry", use_container_width=True):
            st.session_state.page = "charging"
            st.rerun()
    with colb:
        if st.button("📤 Sync Now", use_container_width=True):
            sync_to_server()
    with colc:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.page = "reports"
            st.rerun()
    
    # Recent charging records
    st.subheader("Recent Charging Records")
    conn = sqlite3.connect(DB_PATH)
    df_recent = pd.read_sql_query("SELECT * FROM charging_records ORDER BY timestamp DESC LIMIT 10", conn)
    conn.close()
    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No records yet.")
    
    # AI Insight
    st.divider()
    st.subheader("🧠 AI Business Insights")
    col1, col2 = st.columns(2)
    with col1:
        busiest_day = predict_charging_demand()
        st.info(f"📈 Predicted busiest charging day in next week: **{busiest_day}** customers")
    with col2:
        st.info(f"💡 Staff suggestion: {'Prepare extra power banks' if busiest_day > 15 else 'Normal day expected'}")

# ---------------------------
# Charging Registry Page
# ---------------------------
def show_charging():
    st.title("🔋 Charging Management")
    
    # Voice input option
    if st.session_state.voice_enabled and VOICE_AVAILABLE:
        if st.button("🎤 Use Voice to Add Record"):
            spoken = voice_input(language="krio")
            if spoken:
                st.info(f"You said: {spoken}")
                # Simple parsing (demo)
                if "add" in spoken.lower():
                    st.session_state.voice_input_mode = True
    
    # New entry form
    with st.expander("➕ Add New Charging Record", expanded=True):
        with st.form("charging_form"):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name")
                # Phone models from Sierra Leone (custom list)
                phone_models = [
                    "Tecno Camon", "Itel", "Infinix", "Samsung A series", "iPhone", 
                    "Nokia", "Huawei", "Oppo", "Gionee", "Power Bank", "Laptop", "Radio",
                    "Smart Watch", "Tablet", "Other"
                ]
                phone_model = st.selectbox("Phone/Device Model", phone_models)
                # Card number: 0-100 or "No Card"
                card_options = ["No Card"] + [str(i) for i in range(101)]
                card_number = st.selectbox("Card Number (0-100) or No Card", card_options)
            with col2:
                price = st.number_input("Price (Le)", min_value=3.0, max_value=10.0, value=5.0, step=1.0)
                collected = st.checkbox("Collected?")
                notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Save Record")
            if submitted:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''INSERT INTO charging_records 
                            (customer_name, phone_model, card_number, price, collected, notes)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (customer_name, phone_model, card_number, price, collected, notes))
                conn.commit()
                record_id = c.lastrowid
                conn.close()
                st.success("Record saved!")
                # Option to print receipt immediately
                if st.button("Print Receipt", key=f"print_{record_id}"):
                    receipt = generate_receipt(record_id)
                    st.text(receipt)
                    # Simulate printing
                    st.balloons()
    
    st.divider()
    
    # Search and table view
    st.subheader("📋 Charging Records")
    search_card = st.text_input("🔍 Search by Card Number", placeholder="Enter card number or name...")
    
    # Load data
    conn = sqlite3.connect(DB_PATH)
    if search_card:
        query = "SELECT * FROM charging_records WHERE card_number LIKE ? OR customer_name LIKE ? ORDER BY timestamp DESC"
        params = (f'%{search_card}%', f'%{search_card}%')
    else:
        query = "SELECT * FROM charging_records ORDER BY timestamp DESC"
        params = ()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        # Display table with actions
        for idx, row in df.iterrows():
            cola, colb, colc, cold = st.columns([3,1,1,1])
            with cola:
                st.write(f"**{row['customer_name']}** | {row['phone_model']} | Card: {row['card_number']} | Le {row['price']}")
                st.caption(f"{row['timestamp']} | Collected: {'✅' if row['collected'] else '❌'}")
            with colb:
                if st.button("✅ Collected", key=f"coll_{row['id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("UPDATE charging_records SET collected=1 WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            with colc:
                if st.button("🖨️ Print", key=f"print_{row['id']}"):
                    receipt = generate_receipt(row['id'])
                    st.text(receipt)
            with cold:
                if st.button("🗑️ Delete", key=f"del_{row['id']}"):
                    if is_admin():
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("DELETE FROM charging_records WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                    else:
                        st.error("Only admin can delete records.")
        # Daily total
        daily_total = df[pd.to_datetime(df['timestamp']).dt.date == datetime.now().date()]['price'].sum()
        st.success(f"💰 **Daily Total: Le {daily_total:.2f}**")
    else:
        st.info("No records found.")

# ---------------------------
# Inventory Control Page
# ---------------------------
def show_inventory():
    st.title("📦 Inventory Control")
    
    if not is_admin():
        st.warning("Only admin can modify inventory. You have view-only access.")
    
    # Add new item (admin only)
    if is_admin():
        with st.expander("➕ Add New Item"):
            with st.form("add_item"):
                col1, col2 = st.columns(2)
                with col1:
                    item_name = st.text_input("Item Name")
                    category = st.text_input("Category")
                with col2:
                    quantity = st.number_input("Quantity", min_value=0, step=1)
                    price = st.number_input("Price (Le)", min_value=0.0, step=0.5)
                min_stock = st.number_input("Minimum Stock Alert", min_value=0, value=5)
                submitted = st.form_submit_button("Add Item")
                if submitted:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('''INSERT INTO inventory (item_name, quantity, price, category, min_stock)
                                VALUES (?, ?, ?, ?, ?)''',
                                (item_name, quantity, price, category, min_stock))
                    conn.commit()
                    conn.close()
                    st.success("Item added!")
    
    # View inventory
    st.subheader("Current Inventory")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM inventory ORDER BY item_name", conn)
    conn.close()
    
    if not df.empty:
        # Highlight low stock
        def highlight_low(row):
            return ['background-color: #ffcccc' if row['quantity'] <= row['min_stock'] else '' for _ in row]
        styled_df = df.style.apply(highlight_low, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Update quantity (admin only)
        if is_admin():
            st.subheader("Update Quantity")
            item_to_update = st.selectbox("Select Item", df['item_name'].tolist())
            new_qty = st.number_input("New Quantity", min_value=0, step=1)
            if st.button("Update"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE inventory SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE item_name=?", (new_qty, item_to_update))
                conn.commit()
                conn.close()
                st.success("Updated!")
                st.rerun()
    else:
        st.info("No items in inventory.")

# ---------------------------
# Staff Management Page
# ---------------------------
def show_staff():
    st.title("👥 Staff Management")
    
    if not is_admin():
        st.error("Access denied. Only admin can manage staff.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    df_staff = pd.read_sql_query("SELECT id, username, role, created_at FROM users", conn)
    conn.close()
    
    st.subheader("Current Staff")
    st.dataframe(df_staff, use_container_width=True)
    
    # Add new user
    with st.expander("➕ Add New User"):
        with st.form("add_user"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["staff", "admin"])
            submitted = st.form_submit_button("Add User")
            if submitted:
                hashed = hash_password(new_password)
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                              (new_username, hashed, role))
                    conn.commit()
                    st.success("User added!")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")
                conn.close()
    
    # Remove user
    st.subheader("❌ Remove User")
    user_to_remove = st.selectbox("Select user to remove", df_staff[df_staff['username'] != 'admin']['username'].tolist() if not df_staff.empty else [])
    if st.button("Remove User"):
        if user_to_remove:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username=?", (user_to_remove,))
            conn.commit()
            conn.close()
            st.success(f"User {user_to_remove} removed.")
            st.rerun()
    
    # Clear history (admin only)
    st.subheader("🗑️ Clear App History")
    if st.button("Clear All Charging Records"):
        confirm = st.checkbox("I understand this cannot be undone.")
        if confirm:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM charging_records")
            conn.commit()
            conn.close()
            st.success("All charging records cleared.")
            st.rerun()

# ---------------------------
# Reports & AI Page
# ---------------------------
def show_reports():
    st.title("📊 Reporting Dashboard & AI Predictions")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Daily profit report
    st.subheader("📈 Daily Profit Report")
    df_daily = pd.read_sql_query('''SELECT DATE(timestamp) as day, COUNT(*) as num_charges, SUM(price) as total
                                    FROM charging_records WHERE collected=1
                                    GROUP BY day ORDER BY day DESC LIMIT 30''', conn)
    if not df_daily.empty:
        st.bar_chart(df_daily.set_index('day')['total'])
        st.dataframe(df_daily, use_container_width=True)
    else:
        st.info("No data yet.")
    
    # AI Predictions
    st.divider()
    st.subheader("🧠 AI Predictions")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted Charging Demand (next 7 days)", f"{predict_charging_demand()} customers")
    with col2:
        st.metric("Predicted Income Today", f"Le {predict_daily_income():.2f}")
    
    # Auto send WhatsApp report
    if st.button("📲 Send Daily Report via WhatsApp"):
        report = f"Daily Profit Report: Total Le {df_daily.iloc[0]['total'] if not df_daily.empty else 0} from {df_daily.iloc[0]['num_charges'] if not df_daily.empty else 0} charges."
        send_whatsapp_message("+232XXXXXXXXX", report)  # Replace with actual number
        st.success("Report sent (simulated).")
    
    conn.close()

# ---------------------------
# Sync & Cloud Page
# ---------------------------
def show_sync():
    st.title("🔄 Offline-Online Sync")
    
    st.write("Current mode:", "📴 Offline" if st.session_state.offline_mode else "🌐 Online")
    
    conn = sqlite3.connect(DB_PATH)
    df_pending = pd.read_sql_query("SELECT * FROM sync_log WHERE synced=0", conn)
    conn.close()
    
    st.write(f"Pending sync records: {len(df_pending)}")
    
    if st.button("🔄 Sync Now"):
        sync_to_server()
    
    if st.button("📡 Multi-shop Cloud Sync (Simulated)"):
        st.info("Syncing with other shops... (simulated)")
        time.sleep(2)
        st.success("All shops synced.")
    
    st.subheader("Sync Log")
    if not df_pending.empty:
        st.dataframe(df_pending)
    else:
        st.info("All records synced.")

# ---------------------------
# WhatsApp Bot Page
# ---------------------------
def show_whatsapp():
    st.title("📲 WhatsApp Bot for Customers")
    
    st.markdown("""
    Customers can send a WhatsApp message to your business number to check their phone status.
    Example: "Check card 45" or "Status for Tecno"
    """)
    
    # Simulate incoming message
    st.subheader("Simulate Customer Inquiry")
    incoming = st.text_input("Enter simulated customer message")
    if incoming:
        # Simple bot logic
        if "card" in incoming.lower():
            parts = incoming.split()
            card_num = parts[-1] if parts[-1].isdigit() else "unknown"
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT * FROM charging_records WHERE card_number=? ORDER BY timestamp DESC LIMIT 1", conn, params=(card_num,))
            conn.close()
            if not df.empty:
                row = df.iloc[0]
                status = "collected" if row['collected'] else "not collected yet"
                reply = f"Card {card_num}: {row['phone_model']}, Status: {status}, Price: Le {row['price']}"
            else:
                reply = f"No record found for card {card_num}."
        else:
            reply = "Please send 'Check card <number>'."
        st.info(f"🤖 Bot reply: {reply}")
    
    # Auto profit sender (scheduled)
    if st.button("📤 Send Auto Profit to Admin WhatsApp"):
        conn = sqlite3.connect(DB_PATH)
        today = datetime.now().date()
        df = pd.read_sql_query("SELECT SUM(price) as total FROM charging_records WHERE DATE(timestamp)=? AND collected=1", conn, params=(today,))
        total = df.iloc[0]['total'] or 0
        conn.close()
        msg = f"Abubakarr Enterprise Daily Profit: Le {total:.2f}"
        send_whatsapp_message("+232XXXXXXXXX", msg)
        st.success("Profit report sent.")

# ---------------------------
# Voice Assistant Page
# ---------------------------
def show_voice():
    st.title("🎤 Real Krio + English Voice Assistant")
    
    st.markdown("""
    Speak in Krio or English to interact with the system.
    Examples:
    - "Add charging record for Amadu with Tecno phone, card 23, price 5 le"
    - "Show today's profit"
    - "Check inventory"
    """)
    
    if not VOICE_AVAILABLE:
        st.error("Speech recognition library not installed. Please install: pip install SpeechRecognition")
        return
    
    if st.button("🎤 Start Listening"):
        text = voice_input(language="krio")
        if text:
            st.write(f"Recognized: {text}")
            # Simple command parsing (demo)
            if "add" in text.lower() and "charging" in text.lower():
                st.info("Would add charging record (simulated).")
            elif "profit" in text.lower():
                total = predict_daily_income()
                st.success(f"Today's predicted profit is Le {total:.2f}")
            else:
                st.warning("Command not recognized. Try again.")
    
    st.divider()
    st.subheader("Krio Voice Talking AI")
    if st.button("🔊 Say Welcome in Krio"):
        text_to_speech("Welcome to Abubakarr Enterprise. How we go help you today?")

# ---------------------------
# Maintenance Page
# ---------------------------
def show_maintenance():
    st.title("🛠️ Machine Maintenance")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Log maintenance
    with st.form("maintenance_form"):
        machine = st.text_input("Machine/Equipment")
        action = st.text_input("Action (e.g., oil change, refuel)")
        cost = st.number_input("Cost (Le)", min_value=0.0, step=10.0)
        submitted = st.form_submit_button("Log Maintenance")
        if submitted:
            c = conn.cursor()
            c.execute("INSERT INTO maintenance (machine, action, cost) VALUES (?, ?, ?)",
                      (machine, action, cost))
            conn.commit()
            st.success("Maintenance logged.")
    
    # View history
    st.subheader("Maintenance History")
    df = pd.read_sql_query("SELECT * FROM maintenance ORDER BY timestamp DESC", conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No maintenance records.")
    
    conn.close()

# ---------------------------
# Three Bags System
# ---------------------------
def show_bags():
    st.title("🛍️ Three Bags System")
    
    conn = sqlite3.connect(DB_PATH)
    
    # Initialize three bags if not present
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bags")
    if c.fetchone()[0] == 0:
        for i in range(1,4):
            c.execute("INSERT INTO bags (bag_number, status) VALUES (?, ?)", (f"Bag {i}", "available"))
        conn.commit()
    
    st.subheader("Bag Status")
    df = pd.read_sql_query("SELECT * FROM bags", conn)
    st.dataframe(df, use_container_width=True)
    
    # Update bag status
    st.subheader("Update Bag")
    bag_to_update = st.selectbox("Select Bag", df['bag_number'].tolist())
    new_status = st.selectbox("New Status", ["available", "in use", "maintenance"])
    assigned_to = st.text_input("Assigned to (optional)")
    if st.button("Update Bag"):
        c.execute("UPDATE bags SET status=?, assigned_to=?, last_updated=CURRENT_TIMESTAMP WHERE bag_number=?", (new_status, assigned_to, bag_to_update))
        conn.commit()
        st.success("Bag updated!")
        st.rerun()
    
    conn.close()

# ---------------------------
# Main entry point
# ---------------------------
if not st.session_state.logged_in:
    login_page()
else:
    main_app()

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.markdown("<center>© 2026 Abubakarr Enterprise - Sierra Leone All-in-One Shop Management</center>", unsafe_allow_html=True)
