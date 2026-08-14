import calendar
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class SpendingForecaster:
    """
    Computes statistical and ML spending projections:
    - Current month spending velocity
    - Predicted total spending for current month
    - Expected surplus or budget deficit
    - Predicted spending for next month (overall & per category)
    """

    def generate_forecast(self, user_expenses, user_monthly_budget, target_date=None):
        if target_date is None:
            target_date = date.today()

        user_monthly_budget = float(user_monthly_budget)
        current_year = target_date.year
        current_month = target_date.month
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        day_of_month = target_date.day

        # Filter expenses for current month
        current_month_expenses = [
            e for e in user_expenses 
            if e.date.year == current_year and e.date.month == current_month
        ]

        current_total = sum(float(e.amount) for e in current_month_expenses)
        avg_daily_spent = current_total / day_of_month if day_of_month > 0 else 0

        # Run linear trend regression if we have sufficient daily data
        remaining_days = max(days_in_month - day_of_month, 0)
        
        if len(current_month_expenses) >= 5 and day_of_month >= 3:
            df = pd.DataFrame([{'date': e.date, 'amount': float(e.amount)} for e in current_month_expenses])
            daily_series = df.groupby('date')['amount'].sum().reindex(
                pd.date_range(start=date(current_year, current_month, 1), end=target_date),
                fill_value=0
            )

            X = np.arange(1, len(daily_series) + 1).reshape(-1, 1)
            y = daily_series.values

            reg = LinearRegression().fit(X, y)
            
            # Predict future days in month
            future_X = np.arange(len(daily_series) + 1, days_in_month + 1).reshape(-1, 1)
            if len(future_X) > 0:
                predicted_future_daily = reg.predict(future_X)
                # Clip negative predictions to 0
                predicted_future_daily = np.clip(predicted_future_daily, a_min=0, a_max=None)
                predicted_remaining = float(np.sum(predicted_future_daily))
            else:
                predicted_remaining = 0.0
            
            predicted_total = current_total + predicted_remaining
        else:
            # Simple daily rate projection fallback
            predicted_remaining = avg_daily_spent * remaining_days
            predicted_total = current_total + predicted_remaining

        budget_diff = user_monthly_budget - predicted_total
        will_exceed = predicted_total > user_monthly_budget

        if will_exceed:
            prediction_summary = f"Based on your current daily velocity of ₹{avg_daily_spent:,.0f}/day, you are projected to spend ₹{predicted_total:,.0f} this month, exceeding your ₹{user_monthly_budget:,.0f} budget by ₹{abs(budget_diff):,.0f}."
        else:
            prediction_summary = f"You are likely to remain within your ₹{user_monthly_budget:,.0f} budget with a projected surplus of approximately ₹{budget_diff:,.0f}."

        # Next Month Forecast calculation using historical monthly totals
        next_month_forecast = self._forecast_next_month(user_expenses, user_monthly_budget)

        return {
            'current_spending': round(current_total, 2),
            'days_elapsed': day_of_month,
            'days_remaining': remaining_days,
            'days_in_month': days_in_month,
            'avg_daily_spending': round(avg_daily_spent, 2),
            'predicted_remaining_spending': round(predicted_remaining, 2),
            'predicted_total_spending': round(predicted_total, 2),
            'monthly_budget': round(user_monthly_budget, 2),
            'budget_difference': round(budget_diff, 2),
            'will_exceed_budget': will_exceed,
            'prediction_summary': prediction_summary,
            'next_month_forecast': next_month_forecast,
            'disclaimer': "Predictions are statistical estimations based on past spending velocity and historical patterns. They do not constitute formal financial advice."
        }

    def _forecast_next_month(self, user_expenses, default_budget):
        if not user_expenses:
            return {
                'total': default_budget,
                'by_category': {},
                'evaluation': {
                    'status': 'insufficient_data',
                    'message': 'Not enough historical data for reliable forecasting.'
                }
            }

        df = pd.DataFrame([{
            'amount': float(e.amount),
            'category': e.category,
            'month_key': f"{e.date.year}-{e.date.month:02d}"
        } for e in user_expenses])

        monthly = df.groupby(['month_key', 'category'])['amount'].sum().reset_index()
        months = sorted(df['month_key'].unique())

        # 1. Main Next-Month Forecast
        cat_forecasts = {}
        for category in df['category'].unique():
            cat_data = monthly[monthly['category'] == category]
            recent_vals = []
            for m in reversed(months[-3:]):
                val = cat_data[cat_data['month_key'] == m]['amount']
                recent_vals.append(float(val.values[0]) if len(val) > 0 else 0.0)

            if len(recent_vals) == 3:
                weights = [0.55, 0.30, 0.15]
            elif len(recent_vals) == 2:
                weights = [0.65, 0.35]
            else:
                weights = [1.0]

            weighted_cat_pred = sum(v * w for v, w in zip(recent_vals, weights))
            cat_forecasts[category] = round(weighted_cat_pred, 2)

        total_next_month = sum(cat_forecasts.values())

        # 2. Backtesting Evaluation against Naive Baseline
        # Naive Baseline: Forecast is simply previous month's spending
        eval_result = {
            'status': 'insufficient_data',
            'message': 'Not enough historical data for reliable forecasting.'
        }

        if len(months) >= 3:
            model_errors = []
            baseline_errors = []
            
            # We can backtest starting from month index 2 (third month)
            for i in range(2, len(months)):
                test_month = months[i]
                historical_months = months[:i]
                
                # Actual total spending in test month
                actual_total = float(df[df['month_key'] == test_month]['amount'].sum())
                
                # Model prediction for test month (weighted moving average of historical months)
                # Let's compute it category-by-category using historical_months
                test_cat_forecasts = {}
                for category in df['category'].unique():
                    cat_data = monthly[monthly['category'] == category]
                    recent_vals = []
                    for m in reversed(historical_months[-3:]):
                        val = cat_data[cat_data['month_key'] == m]['amount']
                        recent_vals.append(float(val.values[0]) if len(val) > 0 else 0.0)
                    
                    if len(recent_vals) == 3:
                        w = [0.55, 0.30, 0.15]
                    elif len(recent_vals) == 2:
                        w = [0.65, 0.35]
                    else:
                        w = [1.0]
                    
                    test_cat_forecasts[category] = sum(v * wt for v, wt in zip(recent_vals, w))
                
                model_pred = sum(test_cat_forecasts.values())
                
                # Baseline prediction: previous month's total spending
                prev_month = historical_months[-1]
                baseline_pred = float(df[df['month_key'] == prev_month]['amount'].sum())
                
                model_errors.append(actual_total - model_pred)
                baseline_errors.append(actual_total - baseline_pred)

            if model_errors:
                model_errors_np = np.array(model_errors)
                baseline_errors_np = np.array(baseline_errors)
                
                model_mae = float(np.mean(np.abs(model_errors_np)))
                model_rmse = float(np.sqrt(np.mean(model_errors_np ** 2)))
                
                baseline_mae = float(np.mean(np.abs(baseline_errors_np)))
                baseline_rmse = float(np.sqrt(np.mean(baseline_errors_np ** 2)))
                
                eval_result = {
                    'status': 'success',
                    'message': 'Model successfully evaluated against Naive baseline.',
                    'metrics': {
                        'model_mae': round(model_mae, 2),
                        'model_rmse': round(model_rmse, 2),
                        'baseline_mae': round(baseline_mae, 2),
                        'baseline_rmse': round(baseline_rmse, 2)
                    }
                }

        return {
            'total': round(total_next_month, 2),
            'by_category': cat_forecasts,
            'evaluation': eval_result
        }

forecaster = SpendingForecaster()
