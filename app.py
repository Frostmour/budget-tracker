"""GUI for budget tool"""

import streamlit as st
from budget_logic import (
    CATEGORIES, format_money, create_expense,
    calculate_overall_summary, filter_expenses_by_month,
    calculate_category_totals, calculate_monthly_summary,
    save_data, load_data
)

# Session state
if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "income_by_month" not in st.session_state:
    st.session_state.income_by_month = {}

if "add_expense_key" not in st.session_state:
    st.session_state.add_expense_key = 0

st.sidebar.divider()
st.sidebar.subheader("Set Monthly Income")
income_year = st.sidebar.number_input(
    "Year", min_value=2000, max_value=2100, value=2025, step=1)
income_month = st.sidebar.number_input(
    "Month", min_value=1, max_value=12, value=1, step=1)
income_amount_input = st.sidebar.text_input(
    "Income Amount", placeholder="e.g. 3000.00")


if st.sidebar.button("Set Income"):
    if not income_amount_input.strip():
        st.sidebar.error("Please enter an amount.")
    else:
        try:
            income_amount = float(income_amount_input)
            if income_amount <= 0:
                st.sidebar.error("Amount must be greater than zero.")
            else:
                month_key = f"{int(income_year)}-{int(income_month):02d}"
                st.session_state.income_by_month[month_key] = income_amount
                st.sidebar.success(f"Income set for {month_key}")
        except ValueError:
            st.sidebar.error("Amount must be a valid number.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Add Expense",
    "View Summary",
    "Edit Expense",
    "Delete Expense",
    "Filter by Month",
    "Monthly Summary",
    "Save / Load",
])

# ── Add Expense ──────────────────────────────────────────────
if page == "Add Expense":
    st.title("Add Expense")

    label = st.text_input(
        "Expense name", key=f"label_{st.session_state.add_expense_key}")

    amount_input = st.text_input(
        "Amount", placeholder="e.g. 49.99", key=f"amount_{st.session_state.add_expense_key}")

    category = st.selectbox(
        "Category", CATEGORIES, key=f"category_{st.session_state.add_expense_key}")

    if st.button("Add Expense"):
        if not label.strip():
            st.error("Expense name cannot be empty.")
        elif not amount_input.strip():
            st.error("Please enter an amount.")
        else:
            try:
                amount = float(amount_input)
                if amount <= 0:
                    st.error("Amount must be greater than zero.")
                else:
                    from datetime import datetime
                    date = datetime.now().strftime("%Y-%m-%d")
                    expense = create_expense(
                        label.strip(), amount, category, date)
                    st.session_state.expenses.append(expense)
                    st.success(
                        f"Added: {label} | {category} | {format_money(amount)}")
                    st.session_state.add_expense_key += 1
            except ValueError:
                st.error("Amount must be a valid number.")

    # Live preview of all expenses so far
    if st.session_state.expenses:
        st.divider()
        st.subheader("Expenses so far")
        st.dataframe(
            st.session_state.expenses,
            use_container_width=True
        )

# ── All other pages (placeholders for now) ───────────────────
elif page == "View Summary":
    st.title("View Summary")

    if not st.session_state.expenses and not st.session_state.income_by_month:
        st.info("No data yet. Add some expenses and income first.")
    else:
        # Overall summary table
        summary = calculate_overall_summary(
            st.session_state.income_by_month,
            st.session_state.expenses
        )

        st.subheader("Overall Financials")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", format_money(summary["Total Income"]))
        col2.metric("Total Expenses", format_money(summary["Total Expenses"]))
        col3.metric("Balance", format_money(summary["Overall Balance"]))

        # Category breakdown
        if st.session_state.expenses:
            st.divider()
            st.subheader("Spending by Category")
            category_totals = calculate_category_totals(
                st.session_state.expenses)

            table_data = [
                {"Category": cat, "Total": format_money(amt)}
                for cat, amt in category_totals.items()
            ]
            st.dataframe(table_data, use_container_width=True)

            top_category = max(category_totals, key=category_totals.get)
            st.info(
                f"Top spending category: **{top_category}** — {
                    format_money(category_totals[top_category])}")

elif page == "Edit Expense":
    st.title("Edit Expense")

    if not st.session_state.expenses:
        st.info("No expenses recorded yet.")
    else:
        # Build a readable label for each expense
        options = {
            f"{str(i + 1).zfill(3)}. {e['date']} | {e['label']} | {
                e['category']} | {format_money(e['amount'])}": i
            for i, e in enumerate(st.session_state.expenses)
        }

        selected = st.selectbox(
            "Select an expense to edit", list(options.keys()))
        index = options[selected]
        expense = st.session_state.expenses[index]

        st.divider()
        st.subheader("Edit Fields")

        new_label = st.text_input("Expense name", value=expense["label"])

        new_amount_input = st.text_input(
            "Amount", value=str(expense["amount"]))

        new_category = st.selectbox(
            "Category",
            CATEGORIES,
            index=CATEGORIES.index(expense["category"])
        )

        new_date = st.text_input("Date (YYYY-MM-DD)", value=expense["date"])

        if st.button("Save Changes"):
            # Validate amount
            try:
                new_amount = float(new_amount_input)
                if new_amount <= 0:
                    st.error("Amount must be greater than zero.")
                    st.stop()
            except ValueError:
                st.error("Amount must be a valid number.")
                st.stop()

            # Validate date
            from datetime import datetime
            try:
                datetime.strptime(new_date, "%Y-%m-%d")
            except ValueError:
                st.error("Date must be in YYYY-MM-DD format.")
                st.stop()

            # Validate name
            if not new_label.strip():
                st.error("Expense name cannot be empty.")
                st.stop()

            # Apply changes
            st.session_state.expenses[index]["label"] = new_label.strip()
            st.session_state.expenses[index]["amount"] = new_amount
            st.session_state.expenses[index]["category"] = new_category
            st.session_state.expenses[index]["date"] = new_date
            st.success("Expense updated successfully.")

elif page == "Delete Expense":
    st.title("Delete Expense")

    if not st.session_state.expenses:
        st.info("No expenses recorded yet.")
    else:
        # Build a readable label for each expense
        options = {
            f"{str(i + 1).zfill(3)}. {e['date']} | {e['label']} | {
                e['category']} | {format_money(e['amount'])}": i
            for i, e in enumerate(st.session_state.expenses)
        }

        selected = st.selectbox(
            "Select an expense to delete", list(options.keys()))

        if st.button("Delete Expense"):
            index = options[selected]
            removed = st.session_state.expenses.pop(index)
            st.success(f"Deleted: {removed['label']}")

elif page == "Filter by Month":
    st.title("Filter by Month")

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Year", min_value=2000,
                               max_value=2100, value=2025, step=1)
    with col2:
        month = st.number_input("Month", min_value=1,
                                max_value=12, value=1, step=1)

    if st.button("Filter"):
        filtered = filter_expenses_by_month(
            st.session_state.expenses,
            int(year),
            int(month)
        )

        if not filtered:
            st.warning(f"No expenses found for {int(year)}-{int(month):02d}.")
        else:
            st.success(
                f"Found {len(filtered)} expense(s) for {int(year)}-{int(month):02d}")
            st.dataframe(filtered, use_container_width=True)

            total = sum(e["amount"] for e in filtered)
            st.divider()
            st.metric("Total for period", format_money(total))

elif page == "Monthly Summary":
    st.title("Monthly Summary")

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Year", min_value=2000,
                               max_value=2100, value=2025, step=1)
    with col2:
        month = st.number_input("Month", min_value=1,
                                max_value=12, value=1, step=1)

    if st.button("Show Summary"):
        filtered = filter_expenses_by_month(
            st.session_state.expenses,
            int(year),
            int(month)
        )

        month_label = f"{int(year)}-{int(month):02d}"

        if not filtered:
            st.warning(f"No expenses found for {month_label}.")
        else:
            # Expense summary
            st.subheader(f"Expense Summary for {month_label}")
            total_expenses = sum(e["amount"] for e in filtered)

            category_totals = calculate_category_totals(filtered)
            table_data = [
                {"Category": cat, "Total": format_money(amt)}
                for cat, amt in category_totals.items()
            ]
            st.dataframe(table_data, use_container_width=True)
            st.metric("Total Expenses", format_money(total_expenses))

            # Financial report
            st.divider()
            st.subheader(f"Financial Report for {month_label}")

            summary = calculate_monthly_summary(
                st.session_state.income_by_month,
                st.session_state.expenses,
                int(year),
                int(month)
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("Income", format_money(summary["income"]))
            col2.metric("Expenses", format_money(summary["expenses"]))
            col3.metric("Balance", format_money(summary["balance"]))

elif page == "Save / Load":
    st.title("Save / Load")

    # Save
    st.subheader("Save Data")
    st.write("Saves your current expenses and income to a local file (budget.json).")
    if st.button("Save Data"):
        save_data(st.session_state.income_by_month, st.session_state.expenses)
        st.success("Data saved successfully to budget.json.")

    st.divider()

    # Load
    st.subheader("Load Data")
    st.write("Loads previously saved expenses and income from budget.json.")

    if "confirm_load" not in st.session_state:
        st.session_state.confirm_load = False

    if st.button("Load Data"):
        if st.session_state.expenses or st.session_state.income_by_month:
            st.session_state.confirm_load = True
        else:
            income, expenses = load_data()
            st.session_state.income_by_month = income
            st.session_state.expenses = expenses
            st.success(
                f"Loaded {len(expenses)} expense(s) and {len(income)} month(s) of income.")

    if st.session_state.confirm_load:
        st.warning(
            "You already have data in memory. Loading will overwrite it. Are you sure?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, overwrite"):
                income, expenses = load_data()
                st.session_state.income_by_month = income
                st.session_state.expenses = expenses
                st.session_state.confirm_load = False
                st.success(
                    f"Loaded {len(expenses)} expense(s) and {len(income)} month(s) of income.")
        with col2:
            if st.button("Cancel"):
                st.session_state.confirm_load = False

    st.divider()

    # Export to CSV
    st.subheader("Export to CSV")
    st.write("Downloads your expenses as a CSV file.")

    if st.session_state.expenses:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Label", "Category", "Amount"])
        for e in st.session_state.expenses:
            writer.writerow(
                [e["date"], e["label"], e["category"], e["amount"]])

        st.download_button(
            label="Download CSV",
            data=output.getvalue(),
            file_name="expenses_report.csv",
            mime="text/csv"
        )
    else:
        st.info("No expenses to export yet.")
