from datetime import datetime, date
import pandas as pd
import numpy as np

class InsightEngine:
    """
    Generates dynamic financial insights, spending velocity alerts, recurring subscription lists,
    and smart recommendations based on actual user expense data.
    """

    def generate_insights(self, user_expenses, user_budgets, user_monthly_budget, target_date=None):
        if target_date is None:
            target_date = date.today()

        current_year = target_date.year
        current_month = target_date.month

        # Calculate previous month year & month
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year

        current_expenses = [e for e in user_expenses if e.date.year == current_year and e.date.month == current_month]
        prev_expenses = [e for e in user_expenses if e.date.year == prev_year and e.date.month == prev_month]

        insights = []
        recommendations = []

        curr_total = sum(float(e.amount) for e in current_expenses)
        prev_total = sum(float(e.amount) for e in prev_expenses)

        # 1. Total Spending Change %
        if prev_total > 0:
            total_change_pct = ((curr_total - prev_total) / prev_total) * 100
            if total_change_pct > 15:
                insights.append({
                    'type': 'warning',
                    'title': 'Overall Spending Surge',
                    'message': f"Your spending this month (₹{curr_total:,.0f}) has increased by {total_change_pct:.1f}% compared to last month (₹{prev_total:,.0f})."
                })
            elif total_change_pct < -10:
                insights.append({
                    'type': 'positive',
                    'title': 'Great Savings Velocity',
                    'message': f"You spent {abs(total_change_pct):.1f}% less this month (₹{curr_total:,.0f}) compared to last month (₹{prev_total:,.0f}). Keep it up!"
                })

        # 2. Category Growth & Velocity Analysis
        curr_cat_df = pd.DataFrame([{'category': e.category, 'amount': float(e.amount)} for e in current_expenses]) if current_expenses else pd.DataFrame(columns=['category', 'amount'])
        prev_cat_df = pd.DataFrame([{'category': e.category, 'amount': float(e.amount)} for e in prev_expenses]) if prev_expenses else pd.DataFrame(columns=['category', 'amount'])

        curr_cat_sums = curr_cat_df.groupby('category')['amount'].sum().to_dict() if not curr_cat_df.empty else {}
        prev_cat_sums = prev_cat_df.groupby('category')['amount'].sum().to_dict() if not prev_cat_df.empty else {}

        fastest_growing_cat = None
        max_growth_pct = -999.0

        for cat, curr_amt in curr_cat_sums.items():
            prev_amt = prev_cat_sums.get(cat, 0.0)
            if prev_amt > 500:
                growth_pct = ((curr_amt - prev_amt) / prev_amt) * 100
                if growth_pct > max_growth_pct and growth_pct > 20:
                    max_growth_pct = growth_pct
                    fastest_growing_cat = cat

                if growth_pct >= 20:
                    insights.append({
                        'type': 'warning',
                        'title': f'{cat} Expense Alert',
                        'message': f"You spent {growth_pct:.0f}% more on {cat} this month (₹{curr_amt:,.0f}) compared with last month (₹{prev_amt:,.0f})."
                    })

        if fastest_growing_cat:
            insights.append({
                'type': 'warning',
                'title': 'Fastest-Growing Category',
                'message': f"'{fastest_growing_cat}' is your fastest-growing expense category, increasing by {max_growth_pct:.0f}% month-over-month."
            })
            recommendations.append({
                'type': 'action',
                'title': f'Cap {fastest_growing_cat} Spending',
                'message': f"Consider setting a dedicated category budget for '{fastest_growing_cat}' to restrain rapid acceleration."
            })

        # 3. Category Frequency Insight
        if current_expenses:
            df_curr = pd.DataFrame([{'category': e.category, 'id': e.id} for e in current_expenses])
            top_freq_cat = df_curr.groupby('category')['id'].count().idxmax()
            freq_count = df_curr.groupby('category')['id'].count().max()
            if freq_count >= 5:
                insights.append({
                    'type': 'neutral',
                    'title': 'Frequent Category Purchases',
                    'message': f"You made {freq_count} purchases in the '{top_freq_cat}' category this month."
                })

        # 4. Budget Progress & Threshold Alerts
        category_budgets = {b.category: float(b.amount) for b in user_budgets if b.month == current_month and b.year == current_year}
        for cat, b_amt in category_budgets.items():
            c_spent = curr_cat_sums.get(cat, 0.0)
            if b_amt > 0:
                pct = (c_spent / b_amt) * 100
                if c_spent > b_amt:
                    insights.append({
                        'type': 'warning',
                        'title': f'{cat} Budget Exceeded!',
                        'message': f"You have exceeded your {cat} budget by ₹{c_spent - b_amt:,.2f} ({pct - 100:.0f}%)."
                    })
                elif c_spent == b_amt:
                    insights.append({
                        'type': 'warning',
                        'title': f'{cat} Budget Fully Used',
                        'message': "Budget fully used"
                    })
                elif pct >= 80:
                    insights.append({
                        'type': 'warning',
                        'title': f'{cat} Budget Warning',
                        'message': f"You have used {pct:.0f}% of your {cat} budget."
                    })

        # 5. Recurring Subscriptions Detection
        recurring_expenses = [e for e in user_expenses if e.is_recurring]
        rec_monthly_total = sum(float(e.amount) for e in recurring_expenses if e.date.year == current_year and e.date.month == current_month)
        
        if rec_monthly_total > 0:
            insights.append({
                'type': 'tip',
                'title': 'Recurring Monthly Commitments',
                'message': f"You have ₹{rec_monthly_total:,.0f} in fixed recurring monthly subscriptions (e.g. Rent, Internet, Streaming)."
            })
            recommendations.append({
                'type': 'tip',
                'title': 'Audit Subscriptions',
                'message': f"Review your {len(recurring_expenses)} recurring transactions to identify unused subscriptions or potential annual plan discounts."
            })

        # 6. Default Recommendations if few rules fired
        if len(recommendations) == 0:
            recommendations.append({
                'type': 'tip',
                'title': 'Maintain Balanced Allocation',
                'message': "Your spending distribution looks steady across categories this month."
            })

        return {
            'insights': insights,
            'recommendations': recommendations,
            'recurring_monthly_total': round(rec_monthly_total, 2),
            'recurring_count': len(recurring_expenses)
        }

insight_engine = InsightEngine()
