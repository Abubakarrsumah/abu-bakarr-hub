# --- LIVE INVENTORY VIEW ---
        st.divider()
        st.subheader("📊 Current Stock Levels")

        if not inv_df.empty:
            # 1. Calculate Total Value (Stock * Price) and Total Cost (Stock * Cost)
            inv_df['Total Value (Le)'] = inv_df['Stock'] * inv_df['Price']
            inv_df['Total Cost (Le)'] = inv_df['Stock'] * inv_df['Cost']

            # 2. Display the data table
            st.dataframe(inv_df, use_container_width=True)

            # 3. Show Summary Metrics
            col1, col2 = st.columns(2)
            with col1:
                total_investment = inv_df['Total Cost (Le)'].sum()
                st.metric("Total Investment (Cost)", f"Le {total_investment:,.2f}")
            with col2:
                total_revenue_potential = inv_df['Total Value (Le)'].sum()
                st.metric("Total Potential Revenue", f"Le {total_revenue_potential:,.2f}")
        else:
            st.info("Your inventory is currently empty. Add items above to see them here.")
