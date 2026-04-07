# main.py
from db import session
from models import Category, Expense
from datetime import date

def add_category():
    name = input("Enter category name: ")
    category = Category(name=name)
    session.add(category)
    session.commit()
    print("Category added!")

def add_expense():
    categories = session.query(Category).all()
    if not categories:
        print("No categories found. Add category first.")
        return
    print("Select category:")
    for c in categories:
        print(f"{c.id}: {c.name}")
    cat_id = int(input("Category ID: "))
    amount = float(input("Amount: "))
    note = input("Note: ")
    exp = Expense(amount=amount, category_id=cat_id, note=note, date=date.today())
    session.add(exp)
    session.commit()
    print("Expense added!")

def view_expenses():
    expenses = session.query(Expense).all()
    for e in expenses:
        print(f"{e.id} | {e.amount} | {e.date} | {e.note} | {e.category.name}")

def menu():
    while True:
        print("\n--- Personal Expense Tracker ---")
        print("1. Add Category")
        print("2. Add Expense")
        print("3. View Expenses")
        print("4. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            add_category()
        elif choice == "2":
            add_expense()
        elif choice == "3":
            view_expenses()
        elif choice == "4":
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    menu()