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

def load_data():
    if os.path.exists(DB_CUST): cust = pd.read_csv(DB_CUST)
    else: cust = pd.DataFrame(columns=["Date", "Card #", "Name", "Model", "Status", "Price"])
   
    if os.path.exists(DB_INV): inv = pd.read_csv(DB_INV)
    else: inv = pd.DataFrame([{"Item": "Water 💦", "Stock": 60, "Price": 1.0, "Cost": 0.5}])
   
    if os.path.exists(DB_MAINT): maint = pd.read_csv(DB_MAINT)
    else: maint = pd.DataFrame(columns=["Date", "Action", "Cost", "Next Due"])
   
    if os.path.exists(DB_MISSING): missing = pd.read_csv(DB_MISSING)
    else: missing = pd.DataFrame(columns=["Date", "Card #", "Reason", "Staff"])
   
    return cust, inv, maint, missing

cust_df, inv_df, maint_df, missing_df = load_data()

# --- 2. LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("🏙️ Abu Bakr Enterprise Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pw == "abu123": st.session_state.auth = "admin"; st.rerun()
        elif user == "staff" and pw == "hub456": st.session_state.auth = "staff"; st.rerun()
    st.stop()

# --- 3. SIDEBAR: 3-BAG SYSTEM ---
st.sidebar.title(f"🚀 {st.session_state.auth.upper()} PORTAL")
st.sidebar.divider()
st.sidebar.header("💰 3-Bag System")
total_rev = cust_df['Price'].sum()
bag1_ops = 124.0
bag2_restock = st.sidebar.number_input("Bag 2: Restock Money (Le)", min_value=0.0)
bag3_wealth = total_rev - bag1_ops - bag2_restock - 30

st.sidebar.info(f"💼 Bag 1 (Ops): Le {bag1_ops}")
st.sidebar.info(f"🛒 Bag 2 (Inv): Le {bag2_restock}")
st.sidebar.success(f"💎 Bag 3 (Wealth): Le {max(0.0, bag3_wealth)}")

if st.sidebar.button("Logout"): st.session_state.auth = None; st.rerun()

menu = ["📊 Dashboard", "🔌 Charging Registry", "🛒 Retail Shop", "🔧 Maintenance & Oils", "🚨 Missing Cards", "⚙️ Admin Tools"]
choice = st.sidebar.radio("Go To:", menu)

# --- 4. APP PAGES ---

if choice == "📊 Dashboard":
    st.header("📈 Business Performance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Revenue", f"Le {total_rev}")
    c2.metric("Maint. Cost", f"Le {maint_df['Cost'].sum()}")
    c3.metric("Wealth (Bag 3)", f"Le {max(0.0, bag3_wealth)}")

elif choice == "🔌 Charging Registry":
    # --- PART A: NEW ENTRY FORM ---
    st.subheader("📝 1. New Entry")
    with st.form("reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        card, name = col1.text_input("Card #"), col2.text_input("Customer Name")
        model, fee = col1.text_input("Model"), col2.selectbox("Fee", [3, 5])
        if st.form_submit_button("Save Entry"):
            new_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Card #": card, "Name": name, "Model": model, "Status": "Charging", "Price": fee}
            cust_df = pd.concat([cust_df, pd.DataFrame([new_row])], ignore_index=True)
            cust_df.to_csv(DB_CUST, index=False); st.success("Saved!"); st.rerun()
   
    st.divider()

    # --- PART B: ACTIVE ENTRY TABLE ---
    st.subheader("📋 2. Active Charging List")
    active = cust_df[cust_df['Status'] == "Charging"]
    if active.empty:
        st.info("No phones are currently charging.")
    else:
        st.dataframe(active, use_container_width=True)

    st.divider()

    # --- PART C: COLLECTION CONFIRMATION AREA ---
    st.subheader("✅ 3. Confirm Collection")
    search = st.text_input("🔍 Search Card # or Name to Confirm")
   
    to_confirm = active.copy()
    if search:
        to_confirm = to_confirm[to_confirm.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
   
    if not to_confirm.empty:
        for i, row in to_confirm.iterrows():
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"**Card {row['Card #']}**: {row['Name']} - {row['Model']}")
            if col_btn.button(f"Confirm Collection", key=f"confirm_{i}"):
                cust_df.at[i, 'Status'] = "Collected ✅"
                cust_df.to_csv(DB_CUST, index=False)
                st.success(f"Card {row['Card #']} Collected!")
                st.rerun()

elif choice == "🛒 Retail Shop":
    st.table(inv_df)
    item = st.selectbox("Record Sale", inv_df['Item'].tolist())
    if st.button("Confirm Sale"):
        idx = inv_df.index[inv_df['Item'] == item][0]
        if inv_df.at[idx, 'Stock'] > 0:
            inv_df.at[idx, 'Stock'] -= 1
            inv_df.to_csv(DB_INV, index=False); st.success("Sold!"); st.rerun()

elif choice == "🔧 Maintenance & Oils":
    st.header("🔧 Machine Maintenance")
    with st.form("m_form", clear_on_submit=True):
        act = st.selectbox("Action", ["Oil Change", "Gen Repair", "Cleaning"])
        cost = st.number_input("Cost (Le)", min_value=0.0)
        due = st.date_input("Next Date")
        if st.form_submit_button("Log"):
            m_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Action": act, "Cost": cost, "Next Due": due}
            maint_df = pd.concat([maint_df, pd.DataFrame([m_row])], ignore_index=True)
            maint_df.to_csv(DB_MAINT, index=False); st.success("Logged!"); st.rerun()
    st.dataframe(maint_df)

elif choice == "🚨 Missing Cards":
    st.header("🚨 Missing Card Log")
    with st.form("ms_form", clear_on_submit=True):
        m_card = st.text_input("Card #")
        rsn = st.selectbox("Reason", ["Lost", "Stolen", "Broken"])
        if st.form_submit_button("Report"):
            ms_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Card #": m_card, "Reason": rsn, "Staff": st.session_state.auth}
            missing_df = pd.concat([missing_df, pd.DataFrame([ms_row])], ignore_index=True)
            missing_df.to_csv(DB_MISSING, index=False); st.success("Reported!"); st.rerun()
    st.dataframe(missing_df)

elif choice == "⚙️ Admin Tools":
    if st.session_state.auth == "admin":
        st.header("🔐 Admin Controls")
        with st.expander("➕ Add New Inventory Item"):
            p_name = st.text_input("Item Name")
            p_stk = st.number_input("Qty", 1)
            p_prc = st.number_input("Price", 0.5)
            if st.button("Add Item"):
                new_p = {"Item": p_name, "Stock": p_stk, "Price": p_prc, "Cost": 0.0}
                inv_df = pd.concat([inv_df, pd.DataFrame([new_p])], ignore_index=True)
                inv_df.to_csv(DB_INV, index=False); st.success("Added!"); st.rerun()
        st.divider()
        st.subheader("📁 Download Business Reports")
        st.download_button("Download Sales Report", cust_df.to_csv(index=False), "sales_report.csv", "text/csv")
        st.divider()
        st.subheader("♻️ Monthly Recycle")
        if st.button("♻️ RESET ALL LOGS"):
            pd.DataFrame(columns=["Date", "Card #", "Name", "Model", "Status", "Price"]).to_csv(DB_CUST, index=False)
            pd.DataFrame(columns=["Date", "Action", "Cost", "Next Due"]).to_csv(DB_MAINT, index=False)
            pd.DataFrame(columns=["Date", "Card #", "Reason", "Staff"]).to_csv(DB_MISSING, index=False)
            st.success("Recycled!"); st.rerun()
    else: st.error("Admin Only")
