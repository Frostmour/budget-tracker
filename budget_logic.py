"""Only the logic functions needed for the GUI"""

# imports

import json

import csv

# constants

CATEGORIES = [
    "Housing",
    "Food",
    "Transportation",
    "Utilities",
    "Entertainment",
    "Credit Card",
    "Loans",
    "Other"
]


def format_money(amount):
    """
    :param amount: Amount to be formatted in standard accounting style
    """
    if amount < 0:
        return f"(${abs(amount):,.2f})"
    return f"${amount:,.2f}"


def create_expense(label, amount, category, date):
    """
    Creates an expense dictionary.
    """
    return {
        "label": label,
        "amount": amount,
        "category": category,
        "date": date
    }


def calculate_category_totals(expenses):
    """
    Returns total expenses per category.
    """

    totals = {}

    for expense in expenses:
        category = expense["category"]
        amount = expense["amount"]

        totals[category] = totals.get(category, 0) + amount

    return totals


def filter_expenses_by_month(expenses, year, month):
    """
    Returns a list of expenses for a given year and month.
    Month should be an integer (1-12).
    """

    month_str = f"{year}-{month:02d}"

    return [
        expense for expense in expenses
        if expense.get("date", "").startswith(month_str)
    ]


def calculate_monthly_summary(income_by_month, expenses, year, month):
    """
    Calculates income, expenses and balance for a specific month.
    """

    month_key = f"{year}-{month:02d}"

    income = income_by_month.get(month_key, 0.0)

    monthly_expenses = filter_expenses_by_month(expenses, year, month)

    total_expenses = sum(e["amount"] for e in monthly_expenses)

    balance = income - total_expenses

    return {
        "income": income,
        "expenses": total_expenses,
        "balance": balance
    }


def calculate_overall_summary(income_by_month, expenses):
    """
    Calculates totals for the overall financial summary across all months.
    """

    total_income = sum(income_by_month.values())
    total_expenses = sum(e["amount"] for e in expenses)
    balance = total_income - total_expenses

    return {
        "Total Income": total_income,
        "Total Expenses": total_expenses,
        "Overall Balance": balance
    }


def save_data(income_by_month, expenses, filename="budget.json"):
    """
    :param income_by_month: Monthly income data being saved to file
    :param expenses: Expenses being saved to file
    :param filename: Json file being created
    """
    budget_data = {
        "income_by_month": income_by_month,
        "expenses": expenses
    }

    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(budget_data, file, indent=4)
        print("Data saved successfully.")
    except OSError as error:
        print(f"Error saving data: {error}")


def load_data(filename="budget.json"):
    """
    :param filename: Json file being read
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)

        income_by_month = loaded_data.get("income_by_month", {})
        expenses = loaded_data.get("expenses", [])

        print("Data loaded successfully.")
        return income_by_month, expenses

    except FileNotFoundError:
        print("No saved data found. Starting fresh.")
        return {}, []

    except (json.JSONDecodeError, OSError) as error:
        print(f"Error loading data: {error}")
        return {}, []


def export_to_csv(expenses, filename="expenses_report.csv"):
    """
    Exporting list of Expenses to CSV file
    """
    if not expenses:
        print("\nNo expenses to export.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Date", "Label", "Category", "Amount"])

        for expense in expenses:
            writer.writerow([
                expense["date"],
                expense["label"],
                expense["category"],
                expense["amount"]
            ])

    print(f"\nExpenses exported successfully to {filename}")
