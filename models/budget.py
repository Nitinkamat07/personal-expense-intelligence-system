from datetime import datetime
from models import db

class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)   # e.g. 2026
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'month', 'year', name='unique_user_category_month_year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'amount': round(float(self.amount), 2) if self.amount is not None else 0.0,
            'month': self.month,
            'year': self.year,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Budget {self.category}: {self.amount}>'
