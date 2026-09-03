import plotly.express as px
import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# --- STEP 1: Database Setup ---
if not os.path.exists("receipts"):
    os.makedirs("receipts")

conn = sqlite3.connect('construction_expenses.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        phase TEXT,
        category TEXT,
        vendor TEXT,
        amount REAL,
        receipt_path TEXT
    )
''')
conn.commit()

# --- STEP 2: Page Configuration ---
st.set_page_config(page_title="Home Build Tracker", layout="wide")
st.title("🏗️ Home Construction Expense Tracker")

# --- STEP 3 & 4: Data Entry Form and Processing ---
st.sidebar.header("Log New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", datetime.today())
    phase = st.selectbox("Construction Phase",
                         ["Foundation", "Framing", "Plumbing", "Electrical", "Finishing", "Other"])
    category = st.selectbox("Category", ["Material", "Labor", "Permits/Fees", "Equipment Rental", "Other"])
    vendor = st.text_input("Vendor / Payee")
    amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
    receipt = st.file_uploader("Upload Receipt (Optional)", type=["jpg", "jpeg", "png", "pdf"])

    submitted = st.form_submit_button("Save Expense")

    if submitted:
        if vendor and amount > 0:
            receipt_path = None

            if receipt is not None:
                receipt_path = os.path.join("receipts", receipt.name)
                with open(receipt_path, "wb") as f:
                    f.write(receipt.getbuffer())

            c.execute('''
                INSERT INTO expenses (date, phase, category, vendor, amount, receipt_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (date.strftime("%Y-%m-%d"), phase, category, vendor, amount, receipt_path))

            conn.commit()
            st.sidebar.success("Expense saved successfully!")
        else:
            st.sidebar.error("Please enter a valid Vendor and Amount.")

# --- STEP 5: Upgraded Dashboard ---
st.subheader("Recent Expenses Dashboard")

df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)

if not df.empty:
    total_spent = df['amount'].sum()
    st.metric(label="Total Construction Spend", value=f"₹{total_spent:,.2f}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Spending by Phase**")
        # Group data and create an interactive donut chart
        phase_spend = df.groupby("phase")["amount"].sum().reset_index()
        fig1 = px.pie(phase_spend, values='amount', names='phase', hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("**Spending by Category**")
        # Group data and create an interactive colored bar chart
        category_spend = df.groupby("category")["amount"].sum().reset_index()
        fig2 = px.bar(category_spend, x='category', y='amount', color='category')
        st.plotly_chart(fig2, use_container_width=True)

    # Hide the raw data behind a clean, clickable expander
    with st.expander("🔍 View and Search Raw Expense Records"):
        display_df = df.drop(columns=['id'])
        st.dataframe(display_df, use_container_width=True)
else:
    st.info("No expenses logged yet. Use the sidebar to add your first transaction!")