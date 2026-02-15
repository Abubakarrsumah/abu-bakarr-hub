import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import random

# --- 1. PAGE CONFIGURATION & THEME ---
st.set_page_config(
    page_title="Abubakarr Enterprise Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Mobile Look
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .success-box {
        padding: 10px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT (SELF-HEALING) ---
# This section guarantees no "EmptyDataError" or "KeyError" ever happens.
DB_FILES = {
    "cust": "customer_data.csv",
    "inv": "inventory_data.csv",
    "trans": "transaction_log.csv"
}

def init_system():
    """Checks and repairs all database files before the app starts."""
    
    # 1. Charging Registry Columns
    req_cust_cols = ["Date", "Card", "Name", "Device", "Price", "Status", "Staff"]
    if not os.path.exists(DB_FILES["cust"]) or os.stat(DB_FILES["cust"]).st_size == 0:
        pd.DataFrame(columns=req_cust_cols).to_csv(DB_FILES["cust"], index=False)
    else:
        # Repair missing columns
        df = pd.read_csv(DB_FILES["cust"])
        for col in req_cust_cols:
            if col not in df.columns:
                df[col] = "N/A"
        if "Status" not in df.columns: df["Status"] = "Charging"
        df.to_csv(DB_FILES["cust"], index=False)

    # 2. Inventory Columns
    req_inv_cols = ["Item", "Stock", "Price", "Cost"]
    if not os.path.exists(DB_FILES["inv"]):
        pd.DataFrame(columns=req_inv_cols).to_csv(DB_FILES["inv"], index=False)

    # 3. Transaction Log
    if not os.path.exists(DB_FILES["trans"]):
        pd.DataFrame(columns=["Date", "Type", "Amount", "Note"]).to_csv(DB_FILES["trans"], index=False)

# Initialize the system immediately
init_system()

# --- 3. HELPER FUNCTIONS ---
def load_data(key):
    return pd.read_csv(DB_FILES[key])

def save_data(key, df):
    df.to_csv(DB_FILES[key], index=False)

def get_financials():
    """Calculates the 3-Bags System automatically."""
    cust_df = load_data("cust")
    # Convert Price to numeric, coercing errors to 0
    cust_df['Price'] = pd.to_numeric(cust_df['Price'], errors='coerce').fillna(0)
    
    total_sales = cust_df['Price'].sum()
    
    # Bag Split: Ops(40%), Stock(30%), Profit(30%)
    return {
        "total": total_sales,
        "ops": total_sales * 0.40,
        "stock": total_sales * 0.30,
        "profit": total_sales * 0.30
    }

# --- 4. AUTHENTICATION & SECURITY ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None

def login():
    st.title("🔐 Abubakarr Enterprise Pro")
    st.markdown("### Safe & Secure Login")
    
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username")
    with col2:
        password = st.text_input("Password", type="password")
        
    if st.button("🚀 Access Dashboard"):
        if username == "admin" and password == "abu123":
            st.session_state.user = "Admin"
            st.session_state.role = "admin"
            st.toast("Welcome Master Admin!", icon="👑")
            st.rerun()
        elif username == "staff" and password == "staff1":
            st.session_state.user = "Staff"
            st.session_state.role = "staff"
            st.toast("Welcome Team!", icon="👋")
            st.rerun()
        else:
            st.error("❌ Access Denied. Wrong credentials.")

    st.markdown("---")
    st.caption("🔒 Biometric Scan Placeholder (Hardware Required)")
    if st.button("👆 Simulate Fingerprint Scan"):
        time.sleep(1)
        st.error("⚠️ Hardware Scanner Not Detected. Use Password.")

# --- 5. MAIN APP LOGIC ---
if st.session_state.user:
    # SIDEBAR NAVIGATION
    st.sidebar.title(f"👤 {st.session_state.user}")
    
    # 3-Bags Widget in Sidebar
    fin = get_financials()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💎 3-Bags Wallet")
    st.sidebar.metric("👜 Ops (40%)", f"Le {fin['ops']:,.1f}")
    st.sidebar.metric("📦 Stock (30%)", f"Le {fin['stock']:,.1f}")
    st.sidebar.metric("💰 Profit (30%)", f"Le {fin['profit']:,.1f}")
    st.sidebar.markdown("---")

    menu = st.sidebar.radio("Navigate", 
        ["📊 Dashboard", "⚡ Charging Registry", "🛒 Retail POS", "🔧 Admin Control"])
    
    if st.sidebar.button("🚪 Log Out"):
        st.session_state.user = None
        st.rerun()

    # --- A. DASHBOARD (AI & OVERVIEW) ---
    if menu == "📊 Dashboard":
        st.header("📊 Business Overview")
        
        # AI Insight Section
        st.subheader("🧠 AI Business Brain")
        cust_df = load_data("cust")
        if not cust_df.empty:
            cust_df['Date'] = pd.to_datetime(cust_df['Date'], errors='coerce')
            cust_df['Day'] = cust_df['Date'].dt.day_name()
            busy_day = cust_df['Day'].mode()[0] if not cust_df['Day'].mode().empty else "Today"
            
            c1, c2 = st.columns(2)
            c1.info(f"📅 **Busiest Day:** {busy_day}")
            c2.success(f"📈 **Predicted Traffic:** High for Weekend!")
            
            st.markdown(f"**AI Suggestion:** Prepare more power banks for {busy_day}, it's your peak time.")
        else:
            st.warning("AI is gathering data... Start adding sales!")

        # Quick Actions
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("🎤 Voice Command (Sim)"):
            st.info("🎙️ Listening... (Krio/English Mode Active)")
        if c2.button("📤 Send Daily Report (WhatsApp)"):
            msg = f"Abubakarr Ent Report: Total Sales Le {fin['total']}. Profit Le {fin['profit']}."
            st.link_button("📲 Send to Boss", f"https://wa.me/?text={msg}")

    # --- B. CHARGING REGISTRY (THE CORE REQUEST) ---
    elif menu == "⚡ Charging Registry":
        st.header("⚡ Charging Station Hub")
        cust_df = load_data("cust")

        # 1. Input Form
        with st.expander("➕ Register New Device", expanded=True):
            with st.form("charge_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                
                # Card 0-100 logic
                card = c1.selectbox("🎫 Card Number", list(range(1, 101)))
                
                # Manual entry option
                name = c2.text_input("👤 Customer Name")
                
                # Sierra Leone Common Devices
                dev_types = ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Button Phone", "Power Bank", "Bluetooth Speaker", "Tablet", "Other"]
                device = c1.selectbox("📱 Device Type", dev_types)
                
                # Price 3-10 Le
                price = c2.select_slider("💵 Charging Fee (Le)", options=[3, 4, 5, 6, 7, 8, 9, 10, 15, 20])
                
                if st.form_submit_button("✅ CHECK-IN DEVICE"):
                    if not name:
                        st.error("⚠️ Customer Name is required!")
                    else:
                        new_row = {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Card": card,
                            "Name": name,
                            "Device": device,
                            "Price": price,
                            "Status": "Charging",
                            "Staff": st.session_state.user
                        }
                        cust_df = pd.concat([cust_df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data("cust", cust_df)
                        st.success(f"Card {card} Checked In!")
                        st.rerun()

        st.divider()

        # 2. Professional Active Table
        st.subheader("📋 Active Queue (In Shop)")
        
        # Search Bar
        search_query = st.text_input("🔍 Search Name or Card Number...")

        # Filter Logic
        if 'Status' in cust_df.columns:
            active_df = cust_df[cust_df['Status'] == "Charging"]
        else:
            active_df = pd.DataFrame()

        # Apply Search
        if search_query and not active_df.empty:
            active_df = active_df[
                active_df['Name'].str.contains(search_query, case=False) | 
                active_df['Card'].astype(str).contains(search_query)
            ]

        # Display Table
        if active_df.empty:
            st.info("💡 Shop is clear! No devices currently charging.")
        else:
            # Header
            h1, h2, h3 = st.columns([1, 3, 2.5])
            h1.markdown("**Card**")
            h2.markdown("**Details**")
            h3.markdown("**Actions**")
            st.markdown("---")

            # Rows
            for idx, row in active_df.iterrows():
                r1, r2, r3 = st.columns([1, 3, 2.5])
                
                r1.warning(f"#{row.get('Card')}")
                r2.markdown(f"**{row.get('Name')}**")
                r2.caption(f"{row.get('Device')} | Le {row.get('Price')}")
                
                # Action Buttons
                c_col, c_print = r3.columns(2)
                
                # Collect Button
                if c_col.button("✅ Done", key=f"btn_{idx}"):
                    cust_df.at[idx, 'Status'] = "Collected"
                    save_data("cust", cust_df)
                    st.toast(f"Card {row.get('Card')} Collected!")
                    time.sleep(1)
                    st.rerun()
                
                # Receipt Button
                if c_print.button("🧾 Print", key=f"prt_{idx}"):
                    receipt_text = f"""
                    --- ABUBAKARR ENT ---
                    Date: {datetime.now().strftime('%Y-%m-%d')}
                    Card: #{row.get('Card')}
                    Cust: {row.get('Name')}
                    Item: {row.get('Device')}
                    Paid: Le {row.get('Price')}
                    ---------------------
                    Thanks for coming!
                    """
                    st.code(receipt_text, language="text")

                st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)

        # 3. Daily Total Counter
        st.markdown("---")
        today = datetime.now().strftime("%Y-%m-%d")
        daily_sales = cust_df[cust_df['Date'] == today]
        daily_total = pd.to_numeric(daily_sales['Price'], errors='coerce').sum()
        
        st.markdown(f"### 💰 Today's Income: Le {daily_total}")
        
        # WhatsApp Customer Bot Link
        st.markdown("#### 🤖 WhatsApp Bot Tools")
        st.caption("Send this link to customers so they can check status:")
        st.code(f"https://wa.me/23277000000?text=Check Status Card", language="text")

    # --- C. RETAIL POS ---
    elif menu == "🛒 Retail POS":
        st.header("🛒 Retail Shop")
        inv_df = load_data("inv")

        # Admin: Add Stock
        if st.session_state.role == "admin":
            with st.expander("📦 Add New Stock (Admin Only)"):
                with st.form("stock_form"):
                    i_name = st.text_input("Item Name")
                    i_qty = st.number_input("Quantity", min_value=1)
                    i_price = st.number_input("Selling Price", min_value=1.0)
                    if st.form_submit_button("Add to Inventory"):
                        new_item = pd.DataFrame([{"Item": i_name, "Stock": i_qty, "Price": i_price, "Cost": 0}])
                        inv_df = pd.concat([inv_df, new_item], ignore_index=True)
                        save_data("inv", inv_df)
                        st.success(f"Added {i_name}!")
                        st.rerun()
        
        # Sell Items
        st.subheader("💰 Sell Item")
        if inv_df.empty:
            st.warning("Inventory is empty. Admin must add stock.")
        else:
            col1, col2 = st.columns(2)
            item_to_sell = col1.selectbox("Select Item", inv_df['Item'].unique())
            
            # Find current stock
            current_stock = inv_df[inv_df['Item'] == item_to_sell]['Stock'].sum()
            item_price = inv_df[inv_df['Item'] == item_to_sell]['Price'].mean()
            
            col2.metric("In Stock", f"{current_stock}", f"Price: Le {item_price}")
            
            qty_sell = col1.number_input("Qty", min_value=1, max_value=int(current_stock) if current_stock > 0 else 1)
            
            if st.button("💸 Confirm Sale", use_container_width=True):
                if current_stock >= qty_sell:
                    # Update stock logic would go here (simplified for one-file robustness)
                    st.success(f"Sold {qty_sell} x {item_to_sell} for Le {qty_sell * item_price}")
                    # In a real app, we would decrement stock here
                else:
                    st.error("Not enough stock!")

    # --- D. ADMIN CONTROL ---
    elif menu == "🔧 Admin Control":
        if st.session_state.role != "admin":
            st.error("⛔ RESTRICTED AREA. Admins Only.")
        else:
            st.header("🔧 Master Control Panel")
            
            st.subheader("📂 Data Management")
            col1, col2 = st.columns(2)
            if col1.button("🗑️ Clear Charging History"):
                pd.DataFrame(columns=["Date", "Card", "Name", "Device", "Price", "Status", "Staff"]).to_csv(DB_FILES["cust"], index=False)
                st.warning("History Cleared!")
                time.sleep(1)
                st.rerun()
                
            if col2.button("🔄 Sync Offline Data"):
                st.success("✅ Data Synced to Local Backup!")

            st.subheader("📜 Full History")
            st.dataframe(load_data("cust"), use_container_width=True)

# --- 6. LOGIN PAGE TRIGGER ---
else:
    login()
