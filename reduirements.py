import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Abu Bakr's Business Hub", layout="wide")
st.title("🏙️ Abu Bakr's Charging & Retail Hub")

# --- DATA STORAGE FILES ---
DB_FILE = "customer_log.csv"
SHOP_FILE = "shop_inventory.csv"
MISSING_FILE = "loss_log.csv"

# --- LOAD DATA ---
if os.path.exists(DB_FILE): st.session_state.customers = pd.read_csv(DB_FILE)
else: st.session_state.customers = pd.DataFrame(columns=["Year", "Date", "Card #", "Name", "Model", "Collected", "Price"])

if os.path.exists(MISSING_FILE): st.session_state.missing = pd.read_csv(MISSING_FILE)
else: st.session_state.missing = pd.DataFrame(columns=["Date", "Item", "Quantity", "Reason"])

# --- LOAD SHOP INVENTORY ---
if os.path.exists(SHOP_FILE):
    st.session_state.shop = pd.read_csv(SHOP_FILE)
else:
    # Starting stock as requested
    st.session_state.shop = pd.DataFrame([
        {"Item": "Water 💦", "Stock": 60, "Price": 1.0},
        {"Item": "Milcolac", "Stock": 20, "Price": 5.0},
        {"Item": "Sweets", "Stock": 49, "Price": 1.0},
        {"Item": "Bubble Gum", "Stock": 100, "Price": 0.5}
    ])

# --- SIDEBAR: MONEY ---
st.sidebar.header("💰 Money Management")
total_in = st.sidebar.number_input("Total Cash Today", min_value=0.0)
bag1, bag2 = 124.0, st.sidebar.number_input("Restock Cost", min_value=0.0)
bag3 = total_in - bag1 - bag2 - 30
st.sidebar.write(f"**Bag 3 (Your Wealth): Le {max(0.0, bag3)}**")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["Charging Registry", "Retail & New Stock", "Missing Items", "Reports"])

# --- TAB 1: CHARGING ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Check-In")
        with st.form("charging_form", clear_on_submit=True):
            card_no, name, model = st.text_input("Card #"), st.text_input("Customer Name"), st.text_input("Phone Model")
            fee, year = st.selectbox("Fee", [3, 5]), st.selectbox("Year", [2025, 2026, 2027])
            if st.form_submit_button("Save"):
                new_data = {"Year": year, "Date": datetime.now().strftime("%d-%m"), "Card #": card_no, "Name": name, "Model": model, "Collected": "NO ❌", "Price": fee}
                st.session_state.customers = pd.concat([st.session_state.customers, pd.DataFrame([new_data])], ignore_index=True)
                st.session_state.customers.to_csv(DB_FILE, index=False)
                st.success("Registered!")
    with col2:
        st.subheader("Collection Tracker")
        for i, row in st.session_state.customers.iterrows():
            if row['Collected'] == "NO ❌":
                if st.button(f"Mark Collected: {row['Name']} ({row['Card #']})", key=f"c_{i}"):
                    st.session_state.customers.at[i, 'Collected'] = "YES ✅"
                    st.session_state.customers.to_csv(DB_FILE, index=False)
                    st.rerun()
        st.dataframe(st.session_state.customers.tail(10))

# --- TAB 2: RETAIL & NEW STOCK ---
with tab2:
    col_stock1, col_stock2 = st.columns(2)
   
    with col_stock1:
        st.header("➕ Add New Product / Stock")
        with st.form("add_product_form", clear_on_submit=True):
            p_name = st.text_input("Product Name (e.g., Juice)")
            p_qty = st.number_input("Quantity to Add", min_value=1)
            p_price = st.number_input("Selling Price", min_value=0.1)
            if st.form_submit_button("Update Inventory"):
                # If product exists, add to stock. If not, create new row.
                if p_name in st.session_state.shop['Item'].values:
                    idx = st.session_state.shop.index[st.session_state.shop['Item'] == p_name][0]
                    st.session_state.shop.at[idx, 'Stock'] += p_qty
                    st.session_state.shop.at[idx, 'Price'] = p_price # Update price if it changed
                else:
                    new_item = {"Item": p_name, "Stock": p_qty, "Price": p_price}
                    st.session_state.shop = pd.concat([st.session_state.shop, pd.DataFrame([new_item])], ignore_index=True)
               
                st.session_state.shop.to_csv(SHOP_FILE, index=False)
                st.success(f"Added {p_qty} of {p_name}!")
                st.rerun()

    with col_stock2:
        st.header("🛒 Record a Sale")
        st.table(st.session_state.shop)
        sell_item = st.selectbox("Select Item to Sell", st.session_state.shop['Item'].tolist())
        if st.button("Confirm Sale"):
            idx = st.session_state.shop.index[st.session_state.shop['Item'] == sell_item][0]
            if st.session_state.shop.at[idx, 'Stock'] > 0:
                st.session_state.shop.at[idx, 'Stock'] -= 1
                st.session_state.shop.to_csv(SHOP_FILE, index=False)
                st.success(f"Sold 1 {sell_item}!")
                st.rerun()
            else: st.error("Out of stock!")

# --- TAB 3: LOSSES & TAB 4: REPORTS (Kept same as previous version) ---
with tab3:
    st.header("🚨 Missing Items")
    with st.form("loss"):
        item, qty, rsn = st.text_input("Item"), st.number_input("Qty", 1), st.text_input("Reason")
        if st.form_submit_button("Log Loss"):
            loss = {"Date": datetime.now().strftime("%Y-%m-%d"), "Item": item, "Quantity": qty, "Reason": rsn}
            st.session_state.missing = pd.concat([st.session_state.missing, pd.DataFrame([loss])], ignore_index=True)
            st.session_state.missing.to_csv(MISSING_FILE, index=False)
            st.warning("Loss Logged.")

with tab4:
    st.header("📊 Export")
    st.download_button("Download Full Log", st.session_state.customers.to_csv(index=False), "Full_Report.csv")
