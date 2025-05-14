import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

def dashboard_ui(port = st.session_state.get("dashboard_portfolio")):    
    if st.button("Close"):
        st.session_state["view_dashboard"] = False
        st.rerun()
    date_range = pd.date_range(start=datetime.datetime.now().date(), periods=100, freq='D')
    portfolio_value = np.cumsum(np.random.randn(100) * 1000 + 50000)

    holdings_data = {
        'Asset': ['Apple', 'Microsoft', 'Tesla', 'Amazon', 'Google'],
        'Ticker': ['AAPL', 'MSFT', 'TSLA', 'AMZN', 'GOOG'],
        'Weight (%)': [20, 25, 15, 30, 10],
        'Value ($)': [100000, 125000, 75000, 150000, 50000],
        'Sector': ['Tech', 'Tech', 'Auto', 'E-commerce', 'Tech']
    }
    holdings_df = pd.DataFrame(holdings_data)

    selected_client = port
    start_date = date_range.min()
    end_date = date_range.max()

    # Header
    st.title("💼 Asset Management Dashboard")
    st.markdown(f"**Client:** {selected_client} | **Date Range:** {start_date} to {end_date}")

    # Portfolio Value Chart
    st.subheader("📈 Portfolio Value Over Time")
    fig, ax = plt.subplots()
    ax.plot(date_range, portfolio_value, color='green')
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.set_title("Portfolio Growth")
    st.pyplot(fig)

    # KPIs
    st.subheader("📊 Key Portfolio Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Value", "$500,000")
    col2.metric("YTD Return", "+8.2%")
    col3.metric("Volatility", "12.4%")

    # Asset Allocation
    st.subheader("📎 Asset Allocation")
    fig2, ax2 = plt.subplots()
    ax2.pie(holdings_df['Weight (%)'], labels=holdings_df['Asset'], autopct='%1.1f%%', startangle=90)
    ax2.axis('equal')
    st.pyplot(fig2)

    # Holdings Table
    st.subheader("📃 Portfolio Holdings")
    st.dataframe(holdings_df)

    # Risk & Return
    st.subheader("📌 Risk & Return Metrics")
    st.write("""
    - **Sharpe Ratio:** 1.25  
    - **Max Drawdown:** -6.8%  
    - **Alpha:** 2.3%  
    - **Beta:** 0.87
    """)
