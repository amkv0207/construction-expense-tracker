import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="Home Build Tracker", layout="wide")
st.title("🏗️ Home Construction Expense Tracker")

# --- Google Sheets Connection ---
# Initialize the connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read the existing data
# We use ttl=0 to bypass the cache so the app always fetches the latest data
existing_data = conn.read(ttl=0)

# --- Data Entry Form ---
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
            receipt_name = receipt.name if receipt is not None else "No Receipt"

            # Create a new row of data
            new_row = pd.DataFrame([{
                "date": date.strftime("%Y-%m-%d"),
                "phase": phase,
                "category": category,
                "vendor": vendor,
                "amount": amount,
                "receipt_path": receipt_name
            }])

            # Combine the old data with the new row
            updated_data = pd.concat([existing_data, new_row], ignore_index=True)

            # Write the entire updated dataframe back to Google Sheets
            conn.update(data=updated_data)

            st.sidebar.success("Expense saved successfully to Google Sheets!")
            st.rerun()
        else:
            st.sidebar.error("Please enter a valid Vendor and Amount.")

# --- Dashboard ---
st.subheader("Recent Expenses Dashboard")

# Fetch the most up-to-date data to display
df = conn.read(ttl=0)

if not df.empty and df['amount'].sum() > 0:
    total_spent = df['amount'].sum()
    st.metric(label="Total Construction Spend", value=f"₹{total_spent:,.2f}")

    st.markdown("**All Expense Records**")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No expenses logged yet. Use the sidebar to add your first transaction!")