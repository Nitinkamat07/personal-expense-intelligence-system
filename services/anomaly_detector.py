import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    """
    Detects unusual transactions using a hybrid approach:
    1. Category-specific Statistical Z-Score / IQR thresholds
    2. Global Isolation Forest outlier detection
    """

    def __init__(self, z_threshold=2.5, min_history_records=5):
        self.z_threshold = z_threshold
        self.min_history_records = min_history_records

    def evaluate_expense(self, user_expenses, new_amount, new_category, date_val=None):
        """
        Evaluate if a new expense amount is anomalous relative to the user's historical expenses.
        Returns: (is_anomaly, reason)
        """
        from datetime import date
        new_amount = float(new_amount)
        if date_val is None:
            date_val = date.today()

        if not user_expenses or len(user_expenses) < self.min_history_records:
            # Fallback for initial account state: flag extremely high absolute amounts (> 15,000)
            if new_amount >= 15000:
                return True, f"High initial expense of ₹{new_amount:,.0f} detected without baseline historical spending."
            return False, ""

        df = pd.DataFrame([{
            'amount': float(e.amount),
            'category': e.category,
            'weekday': float(e.date.weekday()) if hasattr(e.date, 'weekday') else 0.0,
            'day': float(e.date.day) if hasattr(e.date, 'day') else 1.0
        } for e in user_expenses])

        # 1. Category specific evaluation
        cat_df = df[df['category'] == new_category]
        if len(cat_df) >= 3:
            cat_amounts = cat_df['amount'].values
            mean_cat = float(np.mean(cat_amounts))
            std_cat = float(np.std(cat_amounts))
            median_cat = float(np.median(cat_amounts))

            # Z-Score check
            if std_cat > 0:
                z_score = (new_amount - mean_cat) / std_cat
                if z_score >= self.z_threshold and new_amount >= median_cat * 2.5:
                    ratio = new_amount / median_cat if median_cat > 0 else new_amount / mean_cat
                    return True, f"₹{new_amount:,.0f} is {ratio:.1f}x higher than your median {new_category} expense (₹{median_cat:,.0f})."
            elif new_amount >= mean_cat * 3 and new_amount > 500:
                return True, f"₹{new_amount:,.0f} is 3x larger than previous uniform {new_category} expenses (₹{mean_cat:,.0f})."

        # 2. Overall Spending Isolation Forest check (using multidimensional features)
        if len(df) >= 10:
            try:
                from config import Config
                categories_list = Config.CATEGORIES
                
                # Features: Amount, Day of Week, Day of Month, Category Index
                features = []
                for e in user_expenses:
                    cat_idx = categories_list.index(e.category) if e.category in categories_list else len(categories_list)
                    features.append([
                        float(e.amount),
                        float(e.date.weekday()) if hasattr(e.date, 'weekday') else 0.0,
                        float(e.date.day) if hasattr(e.date, 'day') else 1.0,
                        float(cat_idx)
                    ])
                
                X = np.array(features)
                clf = IsolationForest(contamination=0.05, random_state=42)
                clf.fit(X)
                
                new_cat_idx = categories_list.index(new_category) if new_category in categories_list else len(categories_list)
                new_features = np.array([[
                    float(new_amount),
                    float(date_val.weekday()),
                    float(date_val.day),
                    float(new_cat_idx)
                ]])
                
                pred = clf.predict(new_features)[0]
                overall_median = float(np.median(df['amount'].values))
                
                if pred == -1 and new_amount > overall_median * 2.0:
                    day_name = date_val.strftime('%A')
                    return True, f"₹{new_amount:,.0f} spent on a {day_name} (day {date_val.day}) is classified as a statistical spending outlier for your typical patterns."
            except Exception as e:
                print(f"Isolation forest evaluation exception: {e}")

        return False, ""

    def batch_evaluate(self, user_expenses):
        """
        Runs batch anomaly evaluation on a list of Expense objects.
        Sets expense.is_anomaly and expense.anomaly_reason on items that haven't been resolved yet.
        """
        if not user_expenses or len(user_expenses) < self.min_history_records:
            return user_expenses

        df = pd.DataFrame([{
            'id': e.id,
            'amount': float(e.amount),
            'category': e.category,
            'status': e.anomaly_status
        } for e in user_expenses])

        for category in df['category'].unique():
            cat_mask = (df['category'] == category)
            cat_amounts = df[cat_mask]['amount'].values

            if len(cat_amounts) < 3:
                continue

            median = float(np.median(cat_amounts))
            q75, q25 = np.percentile(cat_amounts, [75, 25])
            iqr = q75 - q25
            upper_bound = q75 + 1.8 * iqr

            for idx, row in df[cat_mask].iterrows():
                exp = next((e for e in user_expenses if e.id == row['id']), None)
                if not exp or exp.anomaly_status in ['valid', 'incorrect', 'ignored']:
                    continue

                if row['amount'] > upper_bound and row['amount'] >= median * 2.5 and row['amount'] > 1000:
                    exp.is_anomaly = True
                    ratio = row['amount'] / median if median > 0 else 2.0
                    exp.anomaly_reason = f"Unusual amount: ₹{row['amount']:,.0f} is {ratio:.1f}x your median {category} spending (₹{median:,.0f})."

        return user_expenses

anomaly_detector = AnomalyDetector()
