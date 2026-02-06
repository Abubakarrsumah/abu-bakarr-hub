import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. MOBILE & DESKTOP OPTIMIZATION ---
st.set_page_config(page_title="Abu Bakr Enterprise Hub", layout="wide")

# --- 2. DATABASE RECOVERY & LOADING ---
def load_data():
    # We use these exact filenames to make sure no old data is lost
    files = {
        "cust": ("customer_data.csv", ["Date", "Card #", "Name", "Model", "Status", "Price"]),
        "inv": ("inventory_data.csv", ["Item", "Stock", "Price", "Cost"]),
        "maint": ("maintenance_log.csv", ["Date", "Action", "Cost", "Next Due"]),
        "missing": ("missing_cards.csv", ["Date", "Card #", "Reason", "Staff"]),
        "login": ("login_creds.csv", ["role", "user", "pw"])
    }
    data = {}
    for key, (file, cols) in files.items():
        if os.path.exists(file):
            data[key] = pd.read_csv(file)
        else:
            # Default data if files are totally new
            if key == "login":
                data[key] = pd.DataFrame([{"role": "admin", "user": "admin", "pw": "abu123"}, {"role": "staff", "user": "staff", "pw": "hub456"}])
            else:
                data[key] = pd.DataFrame(columns=cols)
    return data["cust"], data["inv"], data["maint"], data["missing"], data[ "login"]

cust_df, inv_df, maint_df, missing_df, login_df = load_data()

# --- 3. SMART LOGIN (NO CAPITAL ERROR) ---
if 'auth' not in st.session_state: st.session_state.auth = None
if not st.session_state.auth:
    st.title("🏙️ Abu Bakr Enterprise Login")
    u_in = st.text_input("Username").lower().strip() # Fixes capital "Staff" error
    p_in = st.text_input("Password", type="password").strip()
    if st.button("Login"):
        user_match = login_df[(login_df['user'].str.lower() == u_in) & (login_df['pw'] == p_in)]
        if not user_match.empty:
            st.session_state.auth = user_match.iloc[0]['role']
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 4. SIDEBAR (3-BAG SYSTEM) ---
st.sidebar.title(f"🚀 {st.session_state.auth.upper()} PORTAL")
st.sidebar.divider()
total_rev = cust_df['Price'].sum()
st.sidebar.info(f"💼 Bag 1 (Ops): Le 124.0")
bag2 = st.sidebar.number_input("Bag 2 (Restock)", 0.0)
st.sidebar.success(f"💎 Bag 3 (Wealth): Le {total_rev - 124.0 - bag2 - 30}")
if st.sidebar.button("Logout"): st.session_state.auth = None; st.rerun()

# --- 4. DYNAMIC SIDEBAR MENU ---
# Standard items for all users
menu = ["📊 Dashboard", "🔌 Charging Registry", "🛒 Retail Shop", "🔧 Maintenance", "🚨 Missing Cards"]

# ONLY add admin Tools if the person logged in is 'admin'
if st.session_state.auth == "admin":
   menu.append("⚙️ admin Tools")

# This creates the sidebar based on the list above
choice = st.sidebar.radio("Go To:", menu)
# --- 5. PAGE LOGIC (RESTORING ALL ITEMS) ---

if choice == "📊 Dashboard":
    st.header("📊 Business Performance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Charging Rev", f"Le {total_rev}")
    c2.metric("Maint. Cost", f"Le {maint_df['Cost'].sum()}")
    c3.metric("Missing Cards", len(missing_df))
   
    st.divider()
    st.subheader("📥 Daily Reports")
   
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_df = cust_df[cust_df['Date'] == today_str]
   
    if not report_df.empty:
        csv_data = report_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Today's Report", data=csv_data, file_name=f"Report_{today_str}.csv")
    else:
        st.info("No data for today yet.")
# --- 🔌 Charging Registry Page Logic ---
if choice == "🔌 Charging Registry":
    st.header("🔌 Charging Registry")
   
    # PART 1: REGISTRATION FORM
    with st.form("reg", clear_on_submit=True):
        st.subheader("📝 1. Register New Device")
        c1, c2 = st.columns(2)
        card = c1.selectbox("Card #", list(range(1, 101)))
        name = c2.text_input("Customer Name")
        mod = c1.selectbox("Phone Model", ["Infinix", "Tecno", "Samsung", "iPhone", "Itel", "Other"])
        fee = c2.select_slider("Select Fee (Le)", options=list(range(3, 11)))
       
        if st.form_submit_button("Save Entry"):
            new = {"Date": datetime.now().strftime("%Y-%m-%d"), "Card #": card, "Name": name, "Model": mod, "Status": "Charging", "Price": fee}
            cust_df = pd.concat([cust_df, pd.DataFrame([new])], ignore_index=True)
            cust_df.to_csv(DB_CUST, index=False)
            st.success(f"Card {card} saved successfully!")
            st.rerun()

    st.divider()

    # PART 2: ACTIVE ENTRY TABLE (Positioned directly below the form)
    st.subheader("📋 2. Active Charging List")
    active = cust_df[cust_df['Status'] == "Charging"]
   
    if not active.empty:
        # Show the table for full visibility
        st.dataframe(active[["Date", "Card #", "Name", "Model", "Price"]], use_container_width=True)
       
        st.divider()
       
        # PART 3: COLLECTION CONFIRMATION
        st.subheader("✅ 3. Confirm Collection")
        search = st.text_input("🔍 Search Card # or Name to Confirm")
       
        if search:
            active = active[active.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
       
        for i, row in active.iterrows():
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"**Card {row['Card #']}**: {row['Name']} ({row['Model']})")
            if col_btn.button(f"Confirm Collection", key=f"coll_{i}"):
                cust_df.at[i, 'Status'] = "Collected ✅"
                cust_df.to_csv(DB_CUST, index=False)
                st.success(f"Card {row['Card #']} marked as Collected!")
                st.rerun()
    else:
        st.info("No phones are currently charging.")
        
elif choice == "🛒 Retail Shop":
    st.header("🛒 Shop Profit")
   
    # Calculate profit for display
    inv_df['Profit'] = inv_df['Price'] - inv_df['Cost']
    st.dataframe(inv_df, use_container_width=True)
   
    # Check if inventory is empty
    if not inv_df.empty:
        item_sell = st.selectbox("Sell Item", inv_df['Item'].tolist())
       
        if st.button("Confirm Sale"):
            # Find the row index for the selected item
            matching_rows = inv_df.index[inv_df['Item'] == item_sell]
           
            if not matching_rows.empty:
                idx = matching_rows[0]  # This creates the 'idx' variable safely
               
                if inv_df.at[idx, 'Stock'] > 0:
                    inv_df.at[idx, 'Stock'] -= 1
                    inv_df.to_csv("inventory_data.csv", index=False)
                    st.success(f"Sold 1 {item_sell}!")
                    st.rerun()
                else:
                    st.error("Out of Stock!")
            else:
                st.error("Item not found in inventory.")
    else:
        st.info("Your inventory is empty. Add items in Admin Tools.")
elif choice == "🔧 Maintenance":
    st.header("🔧 Machine & Oil Log") # Restored!
    with st.form("m_form"):
        act = st.selectbox("Action", ["Oil Change", "Repair", "Cleaning"])
        cost = st.number_input("Cost", 0.0)
        due = st.date_input("Next Date")
        if st.form_submit_button("Log Maintenance"):
            m_row = {"Date": datetime.now().strftime("%Y-%m-%d"), "Action": act, "Cost": cost, "Next Due": str(due)}
            maint_df = pd.concat([maint_df, pd.DataFrame([m_row])], ignore_index=True)
            maint_df.to_csv("maintenance_log.csv", index=False); st.success("Logged!"); st.rerun()
    st.dataframe(maint_df)

elif choice == "🚨 Missing Cards":
    st.header("🚨 Missing Card Report")
   
    # Form to report a new problem
    with st.form("ms_form"):
        mc = st.selectbox("Select Card #", list(range(1, 101)))
        rsn = st.selectbox("Reason", ["Missing", "Destroyed", "Damaged", "Lost"]) # Dropdown is easier for staff
        details = st.text_input("Additional Details (Optional)")
       
        if st.form_submit_button("Submit Report"):
            ms_row = {
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Card #": mc,
                "Reason": f"{rsn}: {details}" if details else rsn,
                "Staff": st.session_state.auth
            }
            # Add to the existing missing_df
            missing_df = pd.concat([missing_df, pd.DataFrame([ms_row])], ignore_index=True)
           
            # SAVE: Note the capital 'F' in False
            missing_df.to_csv("missing_cards.csv", index=False)
           
            st.success(f"Reported: Card {mc} is {rsn}")
            st.rerun()

    st.divider()
    st.subheader("📋 Missing & Destroyed Log")
    st.dataframe(missing_df, use_container_width=True)
          # Add this below your st.dataframe(missing_df)
if not missing_df.empty:
    if st.button("🗑️ Clear All Missing Reports"):
        # Create an empty version of the table
        missing_df = pd.DataFrame(columns=["Date", "Card #", "Reason", "Staff"])
        # Save the empty table over the old file
        missing_df.to_csv("missing_cards.csv", index=False)
        st.success("Missing cards list has been cleared!")
        st.rerun()
        
elif choice == "⚙️ Admin Tools":
    # 1. Check if the logged-in user is an admin
    if st.session_state.auth == "admin":
        st.header("🛠️ Admin Master Control")
       
        # --- FEATURE 1: USER MANAGEMENT ---
        with st.expander("👤 User Management"):
            st.subheader("Add New Staff or Admin")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            new_r = st.selectbox("Assign Role", ["staff", "admin"])
           
            if st.button("➕ Create User"):
                if new_u and new_p:
                    new_user_row = {"role": new_r, "user": new_u, "pw": new_p}
                    # Use login_df which was loaded at the top of your script
                    login_df = pd.concat([login_df, pd.DataFrame([new_user_row])], ignore_index=True)
                    login_df.to_csv("login_creds.csv", index=False)
                    st.success(f"User {new_u} added!")
                    st.rerun()
                else:
                    st.warning("Please enter both a username and password.")

        # --- FEATURE 2: INVENTORY MANAGEMENT ---
        with st.expander("📦 Shop Inventory (Add Stock)"):
            st.subheader("Add New Stock Items")
            with st.form("admin_inv_form"):
                i_name = st.text_input("Item Name")
                i_stock = st.number_input("Quantity", min_value=1)
                i_price = st.number_input("Selling Price (Le)", min_value=0.0)
                i_cost = st.number_input("Cost Price (Le)", min_value=0.0)
               
                if st.form_submit_button("📥 Add Stock"):
                    new_item = {"Item": i_name, "Stock": i_stock, "Price": i_price, "Cost": i_cost}
                    # This fixes the Retail Shop 'empty' error
                    inv_df = pd.concat([inv_df, pd.DataFrame([new_item])], ignore_index=True)
                    inv_df.to_csv("inventory_data.csv", index=False)
                    st.success(f"Added {i_name} to inventory!")
                    st.rerun()

        # --- FEATURE 3: MASTER DOWNLOADS ---
        with st.expander("📊 Business Reports"):
            st.subheader("Download Full System Data")
            # We convert the current dataframes to CSV for the admin to download
            full_report = cust_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Master Report",
                data=full_report,
                file_name="Master_Business_Report.csv",
                mime="text/csv"
            )

        # --- FEATURE 4: CLEAR HISTORY ---
        with st.expander("⚠️ Danger Zone"):
            st.subheader("Clear All App Records")
            if st.button("🗑️ RESET ALL HISTORY"):
                # This clears the files but keeps the column headers
                cust_df.iloc[0:0].to_csv("customer_data.csv", index=False)
                maint_df.iloc[0:0].to_csv("maintenance_log.csv", index=False)
                missing_df.iloc[0:0].to_csv("missing_cards.csv", index=False)
                st.warning("All charging and maintenance history has been deleted.")
                st.rerun()
   
    else:
        # This shows if a 'staff' user tries to click Admin Tools
        st.error("🚫 Access Denied. Only the Admin can use these tools.")
