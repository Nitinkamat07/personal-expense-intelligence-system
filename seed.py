import os
import random
from datetime import datetime, date, timedelta
import pandas as pd
from app import create_app
from models import db, User, Expense, Budget, Insight
from services.categorizer import categorizer
from services.anomaly_detector import anomaly_detector

def seed_database():
    app = create_app()
    with app.app_context():
        print("1. Re-creating Database tables...")
        db.drop_all()
        db.create_all()

        print("2. Training ML Categorizer model on sample dataset...")
        df_sample = pd.read_csv('data/sample_transactions.csv')
        categorizer.train(df_sample['Description'].tolist(), df_sample['Category'].tolist())
        print("-> ML Categorizer model trained successfully!")

        print("3. Creating Demo User...")
        demo_user = User(
            username='demo',
            email='demo@expense.ai',
            monthly_budget=25000.0,
            currency_symbol='₹'
        )
        demo_user.set_password('password123')
        db.session.add(demo_user)
        db.session.commit()
        print(f"-> Demo User created: {demo_user.email} / password123")

        print("4. Generating multi-month realistic transactions (120+ records)...")
        today = date.today()
        expenses_to_add = []

        # Recurring template transactions (Added every month)
        recurring_templates = [
            ("Monthly Apartment Rent", 12000.0, "Rent", "Net Banking"),
            ("Airtel Broadband Fiber", 999.0, "Bills", "UPI"),
            ("Netflix Premium 4K", 649.0, "Entertainment", "Credit Card"),
            ("Spotify Family Sub", 179.0, "Entertainment", "UPI"),
            ("Gym Membership Fee", 1500.0, "Healthcare", "Debit Card"),
            ("Jio Postpaid Mobile", 499.0, "Bills", "UPI")
        ]

        # Regular transaction templates (Randomly distributed across 3 months)
        regular_templates = [
            ("Swiggy Dinner Order", 340.0, "Food", "UPI"),
            ("Zomato Biryani Special", 480.0, "Food", "UPI"),
            ("Starbucks Cappuccino", 280.0, "Food", "Credit Card"),
            ("Blinkit Quick Grocery", 650.0, "Food", "UPI"),
            ("Zepto Daily Milk & Bread", 180.0, "Food", "UPI"),
            ("Uber Ride to Office", 220.0, "Transport", "UPI"),
            ("Ola Cab Ride", 190.0, "Transport", "UPI"),
            ("Auto Rickshaw Station", 80.0, "Transport", "Cash"),
            ("Petrol Pump Fuel", 1200.0, "Transport", "Credit Card"),
            ("Amazon Electronics Cable", 450.0, "Shopping", "Credit Card"),
            ("Flipkart Clothes Sale", 1490.0, "Shopping", "Debit Card"),
            ("Bookmyshow Movie Ticket", 350.0, "Entertainment", "UPI"),
            ("Electricity Utility Bill", 1450.0, "Utilities", "Net Banking"),
            ("Pharmacy Medicine Bill", 320.0, "Healthcare", "UPI"),
            ("Udemy Python Course", 499.0, "Education", "Credit Card"),
            ("Stationery Notebooks", 150.0, "Education", "Cash"),
            ("Dining Out Restaurant", 1250.0, "Food", "Credit Card")
        ]

        # Explicit Anomaly outliers
        anomalies_to_inject = [
            (today - timedelta(days=5), "Unscheduled Flight Ticket Booking", 8500.0, "Travel", "Credit Card", "Emergency weekend flight ticket."),
            (today - timedelta(days=14), "High-End Luxury Watch Purchase", 18500.0, "Shopping", "Credit Card", "Special anniversary gift purchase."),
            (today - timedelta(days=45), "Five Star Resort Stay", 14200.0, "Travel", "Credit Card", "Vacation booking.")
        ]

        # Generate 90 days of transactions
        start_date = today - timedelta(days=90)
        curr_d = start_date

        while curr_d <= today:
            # First day of month -> inject recurring expenses
            if curr_d.day == 1:
                for desc, amt, cat, pm in recurring_templates:
                    expenses_to_add.append(Expense(
                        user_id=demo_user.id,
                        amount=amt,
                        description=desc,
                        category=cat,
                        date=curr_d,
                        payment_method=pm,
                        is_recurring=True,
                        notes="Automated monthly subscription"
                    ))

            # Daily random expenses (1 to 3 items per day)
            num_daily = random.choices([0, 1, 2, 3], weights=[0.2, 0.4, 0.3, 0.1])[0]
            for _ in range(num_daily):
                template = random.choice(regular_templates)
                # Apply small random noise (+/- 15%) to amounts
                variance = random.uniform(0.85, 1.15)
                amt = round(template[1] * variance, 2)
                
                # ML prediction tracking
                pred_cat, conf, _ = categorizer.predict(template[0])

                expenses_to_add.append(Expense(
                    user_id=demo_user.id,
                    amount=amt,
                    description=template[0],
                    category=template[2],
                    date=curr_d,
                    payment_method=template[3],
                    is_recurring=False,
                    predicted_category=pred_cat,
                    prediction_confidence=conf
                ))

            curr_d += timedelta(days=1)

        # Add explicit anomaly outliers
        for dt, desc, amt, cat, pm, notes in anomalies_to_inject:
            expenses_to_add.append(Expense(
                user_id=demo_user.id,
                amount=amt,
                description=desc,
                category=cat,
                date=dt,
                payment_method=pm,
                is_recurring=False,
                is_anomaly=True,
                anomaly_reason=f"₹{amt:,.0f} significantly exceeds your median {cat} spending.",
                notes=notes
            ))

        db.session.add_all(expenses_to_add)
        db.session.commit()
        print(f"-> Saved {len(expenses_to_add)} expenses!")

        print("5. Batch evaluating anomaly detection flags...")
        all_user_exp = Expense.query.filter_by(user_id=demo_user.id).all()
        anomaly_detector.batch_evaluate(all_user_exp)
        db.session.commit()

        print("6. Creating default monthly category budgets...")
        budgets_to_add = [
            Budget(user_id=demo_user.id, category="Food", amount=7000.0, month=today.month, year=today.year),
            Budget(user_id=demo_user.id, category="Transport", amount=4000.0, month=today.month, year=today.year),
            Budget(user_id=demo_user.id, category="Shopping", amount=4000.0, month=today.month, year=today.year),
            Budget(user_id=demo_user.id, category="Entertainment", amount=2500.0, month=today.month, year=today.year),
            Budget(user_id=demo_user.id, category="Bills", amount=3000.0, month=today.month, year=today.year),
            Budget(user_id=demo_user.id, category="Rent", amount=12000.0, month=today.month, year=today.year)
        ]
        db.session.add_all(budgets_to_add)
        db.session.commit()
        print("-> Category budgets created!")

        print("Finished Seeding Database Successfully!")

if __name__ == '__main__':
    seed_database()
