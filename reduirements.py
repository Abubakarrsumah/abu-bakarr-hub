elif choice == "⚙️ Admin Tools":
    st.write("current role:", st.session_state.get("auth"))
   
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
                    login_df = pd.concat([login_df, pd.DataFrame([new_user_row])], ignore_index=True)
                    login_df.to_csv("login_creds.csv", index=False)
                    st.success(f"User {new_u} added!")
                    st.rerun()
                else:
                    st.warning("Please enter both a username and password.")
