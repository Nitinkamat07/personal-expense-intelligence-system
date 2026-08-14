import re
from datetime import date, datetime
import pandas as pd
from models import db, Expense, Budget

class SpendingCopilotService:
    """
    A lightweight, deterministic query processing engine that parses natural language questions
    about personal finances and returns accurate calculations directly from the database.
    Prevents LLM hallucinations and provides 100% data correctness.
    """

    def process_query(self, user, query_text):
        q = query_text.lower().strip()
        
        # 1. Subscriptions / Recurring spending query
        if any(w in q for w in ['subscription', 'recurring', 'fixed', 'membership', ' Netflix', 'spotify']):
            return self._handle_subscriptions(user)

        # 2. Comparison / Increase query
        elif any(w in q for w in ['why', 'increase', 'compare', 'more', 'difference', 'higher']):
            return self._handle_spending_comparison(user)

        # 3. Budget / Remaining query
        elif any(w in q for w in ['budget', 'remaining', 'left', 'limit', 'threshold']):
            return self._handle_budget_status(user)

        # 4. Top spending / Where query
        elif any(w in q for w in ['where', 'most', 'highest', 'top', 'maximum', 'spending category']):
            return self._handle_top_spending(user)
            
        # 5. Default fallback helper
        else:
            return {
                'success': True,
                'query': query_text,
                'answer': (
                    "I can help you understand your spending patterns and manage your budget. "
                    "Try asking me questions like:\n\n"
                    "• *'Where did I spend the most money this month?'*\n"
                    "• *'Why is my spending higher compared to last month?'*\n"
                    "• *'How much of my budget is left?'*\n"
                    "• *'Show me my active recurring subscriptions.'*"
                ),
                'data': {}
            }

    def _handle_subscriptions(self, user):
        today = date.today()
        recurring_expenses = Expense.query.filter_by(
            user_id=user.id,
            is_recurring=True
        ).all()

        if not recurring_expenses:
            return {
                'success': True,
                'query': 'Active subscriptions',
                'answer': "You currently do not have any transactions marked as recurring subscriptions.",
                'data': {'count': 0, 'total': 0.0}
            }

        # Unique subscriptions by description
        df = pd.DataFrame([{
            'description': e.description,
            'amount': float(e.amount),
            'category': e.category,
            'payment_method': e.payment_method
        } for e in recurring_expenses])

        unique_subs = df.groupby('description').first().reset_index()
        total_monthly = float(unique_subs['amount'].sum())
        count = len(unique_subs)

        sub_list_md = "\n".join([
            f"- **{row['description']}**: ₹{row['amount']:,.2f}/month ({row['category']} via {row['payment_method']})"
            for _, row in unique_subs.iterrows()
        ])

        answer = (
            f"You have **{count} active recurring commitments** totaling **₹{total_monthly:,.2f}/month**:\n\n"
            f"{sub_list_md}\n\n"
            f"💡 *Tip: Auditing these subscriptions regularly can help save up to 10-15% of your fixed expenses.*"
        )

        return {
            'success': True,
            'query': 'Active subscriptions',
            'answer': answer,
            'data': {
                'count': count,
                'total': total_monthly,
                'subscriptions': unique_subs.to_dict(orient='records')
            }
        }

    def _handle_spending_comparison(self, user):
        today = date.today()
        curr_year, curr_month = today.year, today.month
        
        if curr_month == 1:
            prev_month, prev_year = 12, curr_year - 1
        else:
            prev_month, prev_year = curr_month - 1, curr_year

        all_expenses = Expense.query.filter_by(user_id=user.id).all()
        
        curr_expenses = [e for e in all_expenses if e.date.year == curr_year and e.date.month == curr_month]
        prev_expenses = [e for e in all_expenses if e.date.year == prev_year and e.date.month == prev_month]

        curr_total = sum(float(e.amount) for e in curr_expenses)
        prev_total = sum(float(e.amount) for e in prev_expenses)
        diff = curr_total - prev_total

        if not prev_expenses:
            return {
                'success': True,
                'query': 'Spending comparison',
                'answer': f"Your total spending for this month is **₹{curr_total:,.2f}**. I don't have enough historical data from last month to make a comparison yet.",
                'data': {'diff': 0.0}
            }

        # Find category level changes
        curr_cats = pd.DataFrame([{'cat': e.category, 'amt': float(e.amount)} for e in curr_expenses])
        prev_cats = pd.DataFrame([{'cat': e.category, 'amt': float(e.amount)} for e in prev_expenses])

        curr_sums = curr_cats.groupby('cat')['amt'].sum().to_dict() if not curr_cats.empty else {}
        prev_sums = prev_cats.groupby('cat')['amt'].sum().to_dict() if not prev_cats.empty else {}

        cat_diffs = {}
        for cat in set(list(curr_sums.keys()) + list(prev_sums.keys())):
            cat_diffs[cat] = curr_sums.get(cat, 0.0) - prev_sums.get(cat, 0.0)

        highest_increase_cat = max(cat_diffs, key=cat_diffs.get)
        highest_increase_val = cat_diffs[highest_increase_cat]

        # Find the single largest transaction in that increased category
        cat_expenses = [e for e in curr_expenses if e.category == highest_increase_cat]
        largest_txn = max(cat_expenses, key=lambda x: x.amount) if cat_expenses else None

        if diff > 0:
            pct = (diff / prev_total) * 100
            answer = (
                f"Your spending has **increased by ₹{diff:,.2f} (+{pct:.1f}%)** MoM. "
                f"Last month you spent ₹{prev_total:,.2f}, and this month you spent ₹{curr_total:,.2f}.\n\n"
                f"📈 The primary driver of this increase is the **{highest_increase_cat}** category, which grew by **₹{highest_increase_val:,.2f}**.\n"
            )
            if largest_txn:
                answer += f"The single largest transaction in {highest_increase_cat} was **'{largest_txn.description}'** costing **₹{largest_txn.amount:,.2f}** on {largest_txn.date.strftime('%b %d')}."
        else:
            pct = (abs(diff) / prev_total) * 100
            answer = (
                f"Great news! Your spending has **decreased by ₹{abs(diff):,.2f} (-{pct:.1f}%)** MoM. "
                f"Last month you spent ₹{prev_total:,.2f}, compared to ₹{curr_total:,.2f} this month.\n\n"
                f"📉 The largest saving was in the **{highest_increase_cat}** category, where spending dropped by **₹{abs(highest_increase_val):,.2f}**."
            )

        return {
            'success': True,
            'query': 'Spending comparison',
            'answer': answer,
            'data': {
                'current_total': curr_total,
                'previous_total': prev_total,
                'difference': diff,
                'driver_category': highest_increase_cat,
                'driver_amount': highest_increase_val
            }
        }

    def _handle_budget_status(self, user):
        today = date.today()
        curr_year, curr_month = today.year, today.month

        expenses = Expense.query.filter_by(user_id=user.id).all()
        m_expenses = [e for e in expenses if e.date.year == curr_year and e.date.month == curr_month]
        total_spent = sum(float(e.amount) for e in m_expenses)
        
        overall_budget = float(user.monthly_budget or 25000.0)
        remaining = overall_budget - total_spent
        pct_used = (total_spent / overall_budget) * 100 if overall_budget > 0 else 0.0

        if remaining > 0:
            status_text = f"You have **₹{remaining:,.2f}** remaining in your overall budget of **₹{overall_budget:,.2f}** ({pct_used:.1f}% utilized)."
        else:
            status_text = f"🚨 You have **exceeded your overall budget by ₹{abs(remaining):,.2f}** ({pct_used:.1f}% utilized of ₹{overall_budget:,.2f})."

        # Check category specific budgets
        budgets = Budget.query.filter_by(user_id=user.id, month=curr_month, year=curr_year).all()
        cat_spending = {}
        for e in m_expenses:
            cat_spending[e.category] = cat_spending.get(e.category, 0.0) + float(e.amount)

        over_budget_cats = []
        for b in budgets:
            spent = cat_spending.get(b.category, 0.0)
            b_amount_f = float(b.amount)
            if spent > b_amount_f:
                over_budget_cats.append(f"- **{b.category}**: spent ₹{spent:,.2f} of ₹{b_amount_f:,.2f} (Over by ₹{spent - b_amount_f:,.2f})")

        if over_budget_cats:
            status_text += "\n\nCategory Budget Violations:\n" + "\n".join(over_budget_cats)

        return {
            'success': True,
            'query': 'Budget status',
            'answer': status_text,
            'data': {
                'overall_budget': overall_budget,
                'total_spent': total_spent,
                'remaining': remaining,
                'percentage': pct_used
            }
        }

    def _handle_top_spending(self, user):
        today = date.today()
        curr_year, curr_month = today.year, today.month

        expenses = Expense.query.filter_by(user_id=user.id).all()
        m_expenses = [e for e in expenses if e.date.year == curr_year and e.date.month == curr_month]
        
        if not m_expenses:
            return {
                'success': True,
                'query': 'Top spending category',
                'answer': "You have not recorded any expenses for this month yet.",
                'data': {}
            }

        df = pd.DataFrame([{'category': e.category, 'amount': float(e.amount)} for e in m_expenses])
        cat_totals = df.groupby('category')['amount'].sum().reset_index()
        cat_totals = cat_totals.sort_values(by='amount', ascending=False)

        top_cat = cat_totals.iloc[0]['category']
        top_amt = cat_totals.iloc[0]['amount']
        total_month = cat_totals['amount'].sum()
        pct = (top_amt / total_month) * 100

        # Formulate response
        answer = (
            f"Your **highest spending category** this month is **{top_cat}** at **₹{top_amt:,.2f}**, "
            f"which represents **{pct:.1f}%** of your total monthly spending (₹{total_month:,.2f}).\n\n"
            f"Here is the breakdown of your spending by category:\n"
        )
        for _, row in cat_totals.iterrows():
            row_pct = (row['amount'] / total_month) * 100
            answer += f"- **{row['category']}**: ₹{row['amount']:,.2f} ({row_pct:.1f}%)\n"

        return {
            'success': True,
            'query': 'Top spending category',
            'answer': answer,
            'data': {
                'top_category': top_cat,
                'top_amount': top_amt,
                'category_breakdown': cat_totals.to_dict(orient='records')
            }
        }

copilot_service = SpendingCopilotService()
