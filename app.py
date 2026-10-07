import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import re
import os
import base64
import smtplib
from email.mime.text import MIMEText


# ---------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------

st.set_page_config(
    page_title="Receipt & Expense Tracker",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Receipt & Expense Tracker")
st.write(
    "Upload your receipt and let AI extract the expense details."
)


# ---------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# ---------------------------------------------------
# GMAIL SMTP FUNCTION
# ---------------------------------------------------

def send_email_summary(subject, message, receiver_email):

    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["password"]

    email = MIMEText(
        message,
        "plain"
    )

    email["to"] = receiver_email
    email["from"] = sender_email
    email["subject"] = subject

    with smtplib.SMTP(
        "smtp.gmail.com",
        587
    ) as server:

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.sendmail(
            sender_email,
            receiver_email,
            email.as_string()
        )


# ---------------------------------------------------
# CSV FILE
# ---------------------------------------------------

csv_file = "expenses.csv"


# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

st.divider()
st.header("📊 Expense Dashboard")


# Default values
total_expenses = 0
total_transactions = 0
total_categories = 0
category_total = pd.Series(dtype=float)
df = pd.DataFrame()


if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:

    df = pd.read_csv(csv_file)

    if not df.empty:

        # ---------------------------------------------------
        # CONVERT TOTAL TO NUMBERS
        # ---------------------------------------------------

        df["Total"] = pd.to_numeric(
            df["Total"],
            errors="coerce"
        ).fillna(0)


        # ---------------------------------------------------
        # MAIN METRICS
        # ---------------------------------------------------

        total_expenses = df["Total"].sum()

        total_transactions = len(df)

        total_categories = df["Category"].nunique()


        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "💰 Total Expenses",
                f"₹{total_expenses:.2f}"
            )

        with col2:
            st.metric(
                "🧾 Transactions",
                total_transactions
            )

        with col3:
            st.metric(
                "🛒 Categories",
                total_categories
            )


        # ---------------------------------------------------
        # EXPENSE HISTORY
        # ---------------------------------------------------

        st.subheader("📋 Expense History")

        st.dataframe(
            df,
            width="stretch"
        )


        # ---------------------------------------------------
        # CATEGORY-WISE SPENDING
        # ---------------------------------------------------

        category_total = df.groupby(
            "Category"
        )["Total"].sum()

        with st.expander(
            "📊 View Category-wise Spending"
        ):

            st.bar_chart(
                category_total,
                height=220
            )


        # ---------------------------------------------------
        # MONTHLY EXPENSE SUMMARY
        # ---------------------------------------------------

        st.subheader("📅 Monthly Expense Summary")

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce",
            dayfirst=True
        )

        valid_dates = df.dropna(
            subset=["Date"]
        )


        if not valid_dates.empty:

            monthly_total = (
                valid_dates
                .groupby(
                    valid_dates["Date"].dt.to_period("M")
                )["Total"]
                .sum()
            )


            latest_month = monthly_total.index[-1]


            latest_month_data = valid_dates[
                valid_dates["Date"].dt.to_period("M")
                == latest_month
            ]


            month_expense = latest_month_data[
                "Total"
            ].sum()


            average_expense = latest_month_data[
                "Total"
            ].mean()


            highest_expense = latest_month_data[
                "Total"
            ].max()


            # ---------------------------------------------------
            # MONTHLY METRICS
            # ---------------------------------------------------

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "💰 This Month",
                    f"₹{month_expense:.2f}"
                )

            with col2:
                st.metric(
                    "📈 Average Transaction",
                    f"₹{average_expense:.2f}"
                )

            with col3:
                st.metric(
                    "🔝 Highest Expense",
                    f"₹{highest_expense:.2f}"
                )


            # ---------------------------------------------------
            # MONTHLY GRAPH
            # ---------------------------------------------------

            monthly_chart = monthly_total.copy()

            monthly_chart.index = (
                monthly_chart.index.astype(str)
            )

            with st.expander(
                "📅 View Monthly Spending"
            ):

                st.bar_chart(
                    monthly_chart,
                    height=220
                )

        else:

            st.info(
                "No valid dates available for monthly summary."
            )


        # ---------------------------------------------------
        # AI SPENDING INSIGHTS
        # ---------------------------------------------------

        st.divider()

        st.subheader("🤖 AI Spending Insights")

        st.write(
            "Let Gemini analyze your expenses and provide "
            "simple spending insights."
        )


        if st.button(
            "✨ Generate AI Insights"
        ):

            with st.spinner(
                "AI is analyzing your spending..."
            ):

                expense_data = df.to_string(
                    index=False
                )


                insight_prompt = f"""
You are a personal expense analysis assistant.

Analyze the following expense data:

{expense_data}

IMPORTANT:

- All expenses are in Indian Rupees (INR).
- Always use the ₹ symbol for money.
- NEVER use $, USD, or any other currency.
- Do not convert the amounts into another currency.

Give a simple and useful spending analysis.

Include:

1. Total spending
2. Highest spending category
3. Highest individual expense
4. General spending pattern
5. One practical suggestion to save money

Keep the response short and easy to understand.
"""


                try:

                    insight_response = client.models.generate_content(

                        model="gemini-3.8-flash",

                        contents=insight_prompt,

                        config=types.GenerateContentConfig(

                            automatic_function_calling=
                            types.AutomaticFunctionCallingConfig(
                                disable=True
                            )

                        )

                    )


                    if insight_response.text:

                        st.success(
                            "✅ AI analysis completed!"
                        )

                        st.write(
                            insight_response.text
                        )

                    else:

                        st.error(
                            "❌ Gemini returned an empty response."
                        )


                except Exception as e:

                    st.error(
                        f"❌ Gemini AI error: {e}"
                    )


# ---------------------------------------------------
# EMAIL EXPENSE SUMMARY
# ---------------------------------------------------

st.divider()

st.subheader("📧 Email Expense Summary")

st.write(
    "Enter an email address to receive your expense summary."
)


receiver_email = st.text_input(
    "📧 Enter recipient email address",
    placeholder="example@gmail.com"
)


if st.button(
    "📧 Send Email Summary"
):

    if not receiver_email:

        st.warning(
            "⚠️ Please enter an email address."
        )


    elif (
        "@" not in receiver_email
        or "." not in receiver_email
    ):

        st.warning(
            "⚠️ Please enter a valid email address."
        )


    elif df.empty:

        st.warning(
            "⚠️ No expense data available to send."
        )


    else:

        email_message = f"""
💰 Receipt & Expense Tracker

Total Expenses: ₹{total_expenses:.2f}

Transactions: {total_transactions}

Categories: {total_categories}

📊 Category-wise Spending:

{category_total.to_string()}

Thank you for using Receipt & Expense Tracker!
"""


        try:

            send_email_summary(
                "Receipt & Expense Tracker - Expense Summary",
                email_message,
                receiver_email
            )


            st.success(
                f"✅ Expense summary sent successfully to {receiver_email}!"
            )


        except Exception as e:

            st.error(
                f"❌ Email could not be sent: {e}"
            )


# ---------------------------------------------------
# RECEIPT UPLOAD
# ---------------------------------------------------

st.divider()

st.subheader("📸 Upload Receipt")


uploaded_file = st.file_uploader(
    "Upload a receipt image",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file:

    st.image(
        uploaded_file,
        caption="Uploaded Receipt",
        width=400
    )


    if st.button(
        "🤖 Analyze Receipt"
    ):

        with st.spinner(
            "AI is analyzing your receipt..."
        ):


            # ---------------------------------------------------
            # GEMINI PROMPT
            # ---------------------------------------------------

            prompt = """
Analyze this receipt image carefully.

Extract:

1. Store or shop name
2. Date of purchase
3. Total amount
4. Items purchased
5. Expense category

Return the result in this exact format:

Store:
Date:
Total:
Items:
Category:

If any information is not visible,
write "Not available".
"""


            # ---------------------------------------------------
            # IMAGE
            # ---------------------------------------------------

            image_part = types.Part.from_bytes(

                data=uploaded_file.getvalue(),

                mime_type=uploaded_file.type

            )


            # ---------------------------------------------------
            # GEMINI VISION
            # ---------------------------------------------------

            try:

                response = client.models.generate_content(

                    model="gemini-3.8-flash",

                    contents=[
                        prompt,
                        image_part
                    ],

                    config=types.GenerateContentConfig(

                        automatic_function_calling=
                        types.AutomaticFunctionCallingConfig(
                            disable=True
                        )

                    )

                )


                # ---------------------------------------------------
                # DISPLAY RESULT
                # ---------------------------------------------------

                if not response.text:

                    st.error(
                        "❌ Gemini returned an empty response."
                    )

                    st.stop()


                st.success(
                    "✅ Receipt analyzed successfully!"
                )


                st.subheader(
                    "📋 Extracted Expense Details"
                )


                st.write(
                    response.text
                )


                # ---------------------------------------------------
                # EXTRACT INFORMATION
                # ---------------------------------------------------

                result = response.text


                # Store
                store = re.search(
                    r"Store:\s*(.*?)(?=\s*Date:)",
                    result,
                    re.IGNORECASE | re.DOTALL
                )


                # Date
                date = re.search(
                    r"Date:\s*(.*?)(?=\s*Total:)",
                    result,
                    re.IGNORECASE | re.DOTALL
                )


                # Total
                total = re.search(
                    r"Total:\s*₹?\s*([\d,.]+)",
                    result,
                    re.IGNORECASE
                )


                # Category
                category = re.search(
                    r"Category:\s*(.*?)(?:\n|$)",
                    result,
                    re.IGNORECASE
                )


                store_name = (

                    store.group(1).strip()

                    if store

                    else "Not available"

                )


                purchase_date = (

                    date.group(1).strip()

                    if date

                    else "Not available"

                )


                total_amount = (

                    total.group(1).replace(",", "")

                    if total

                    else "0"

                )


                expense_category = (

                    category.group(1)
                    .strip()
                    .replace("*", "")

                    if category

                    else "Other"

                )


                # ---------------------------------------------------
                # CREATE EXPENSE DATA
                # ---------------------------------------------------

                new_expense = pd.DataFrame([{

                    "Store": store_name,

                    "Date": purchase_date,

                    "Total": float(total_amount),

                    "Category": expense_category

                }])


                # ---------------------------------------------------
                # SAVE TO CSV
                # ---------------------------------------------------

                if (

                    os.path.exists(csv_file)

                    and os.path.getsize(csv_file) > 0

                ):

                    new_expense.to_csv(

                        csv_file,

                        mode="a",

                        header=False,

                        index=False

                    )

                else:

                    new_expense.to_csv(

                        csv_file,

                        index=False

                    )


                st.success(
                    "💾 Expense saved successfully!"
                )


                st.info(
                    "🔄 Refresh the page to update the dashboard."
                )


            except Exception as e:

                st.error(
                    f"❌ Receipt analysis failed: {e}"
                )