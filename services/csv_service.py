import io
import csv
from datetime import datetime, timezone
import pandas as pd
from services.categorizer import categorizer
from services.anomaly_detector import anomaly_detector
from models import Expense, db

class CSVService:
    """
    Handles CSV import, header normalization, duplicate transaction detection,
    missing category auto-classification, and CSV data export generation.
    """

    ALLOWED_HEADER_MAP = {
        'date': ['date', 'transaction_date', 'txn_date', 'timestamp'],
        'description': ['description', 'desc', 'narration', 'particulars', 'title'],
        'amount': ['amount', 'amt', 'value', 'price'],
        'category': ['category', 'cat', 'type'],
        'payment_method': ['payment_method', 'payment', 'method', 'mode']
    }

    def process_csv_import(self, file_stream, user_id, user_expenses):
        """
        Parses CSV input, normalizes columns, validates rows, predicts missing categories,
        checks for duplicates against user's existing expenses, and saves valid records to DB.
        Returns detailed import stats summary.
        """
        try:
            content = file_stream.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to parse CSV file: {str(e)}",
                'imported': 0, 'skipped': 0, 'duplicates': 0, 'invalid': 0
            }

        # Normalize column headers to lowercase strip
        df.columns = [str(c).strip().lower() for c in df.columns]

        col_map = {}
        for target_col, synonyms in self.ALLOWED_HEADER_MAP.items():
            found = next((c for c in synonyms if c in df.columns), None)
            if found:
                col_map[target_col] = found

        if 'amount' not in col_map or 'description' not in col_map:
            return {
                'success': False,
                'error': "CSV missing required 'amount' or 'description' column headers.",
                'imported': 0, 'skipped': 0, 'duplicates': 0, 'invalid': 0
            }

        existing_hashes = {
            f"{e.date.strftime('%Y-%m-%d')}_{e.description.lower().strip()}_{float(e.amount)}"
            for e in user_expenses
        }

        imported_count = 0
        skipped_count = 0
        duplicate_count = 0
        invalid_count = 0

        new_expense_objects = []

        for idx, row in df.iterrows():
            # Parse Amount
            raw_amt = row.get(col_map['amount'])
            try:
                if pd.isna(raw_amt):
                    invalid_count += 1
                    continue
                # Clean currency symbols or commas
                amt_str = str(raw_amt).replace('₹', '').replace('$', '').replace(',', '').strip()
                amount = float(amt_str)
                if amount <= 0:
                    invalid_count += 1
                    continue
            except (ValueError, TypeError):
                invalid_count += 1
                continue

            # Parse Description
            raw_desc = row.get(col_map['description'])
            if pd.isna(raw_desc) or not str(raw_desc).strip():
                invalid_count += 1
                continue
            description = str(raw_desc).strip()

            # Parse Date
            raw_date = row.get(col_map.get('date', 'date'))
            parsed_date = self._parse_date(raw_date)

            # Duplicate Check
            hash_key = f"{parsed_date.strftime('%Y-%m-%d')}_{description.lower()}_{amount}"
            if hash_key in existing_hashes:
                duplicate_count += 1
                skipped_count += 1
                continue

            existing_hashes.add(hash_key)

            # Category auto-detection if missing or 'Other'
            raw_cat = row.get(col_map.get('category', 'category'))
            if pd.isna(raw_cat) or str(raw_cat).strip().lower() in ['', 'nan', 'other', 'none', 'uncategorized']:
                pred_cat, conf, _ = categorizer.predict(description)
                category = pred_cat
                predicted_cat = pred_cat
                pred_conf = conf
            else:
                category = str(raw_cat).strip().title()
                predicted_cat = None
                pred_conf = None

            # Payment method
            raw_method = row.get(col_map.get('payment_method', 'payment_method'))
            payment_method = str(raw_method).strip().title() if not pd.isna(raw_method) and str(raw_method).strip() else "UPI"

            # Create model instance
            exp = Expense(
                user_id=user_id,
                amount=amount,
                description=description,
                category=category,
                date=parsed_date,
                payment_method=payment_method,
                predicted_category=predicted_cat,
                prediction_confidence=pred_conf
            )

            # Check anomaly
            is_anom, reason = anomaly_detector.evaluate_expense(user_expenses + new_expense_objects, amount, category, date_val=parsed_date)
            if is_anom:
                exp.is_anomaly = True
                exp.anomaly_reason = reason

            new_expense_objects.append(exp)
            imported_count += 1

        if new_expense_objects:
            db.session.add_all(new_expense_objects)
            db.session.commit()

        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'duplicates': duplicate_count,
            'invalid': invalid_count,
            'total_rows': len(df)
        }

    def export_expenses_csv(self, user_expenses):
        """
        Generates a CSV string download payload from a list of user Expense models.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow(['ID', 'Date', 'Description', 'Amount', 'Category', 'Payment Method', 'Is Recurring', 'Notes', 'Anomaly Flag'])

        for e in user_expenses:
            writer.writerow([
                e.id,
                e.date.strftime('%Y-%m-%d'),
                e.description,
                f"{e.amount:.2f}",
                e.category,
                e.payment_method,
                'Yes' if e.is_recurring else 'No',
                e.notes or '',
                'Yes' if e.is_anomaly else 'No'
            ])

        return output.getvalue()

    def _parse_date(self, raw_date):
        if pd.isna(raw_date) or not raw_date:
            return datetime.now(timezone.utc).date()
        
        date_str = str(raw_date).strip()
        formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y',
            '%Y/%m/%d', '%b %d, %Y', '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
                
        return datetime.now(timezone.utc).date()

csv_service = CSVService()
