from datetime import datetime, date
from models import db

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    payment_method = db.Column(db.String(50), default='UPI')
    notes = db.Column(db.Text, nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    
    # Intelligence fields
    predicted_category = db.Column(db.String(50), nullable=True)
    prediction_confidence = db.Column(db.Float, nullable=True)
    is_anomaly = db.Column(db.Boolean, default=False, index=True)
    anomaly_reason = db.Column(db.String(255), nullable=True)
    anomaly_status = db.Column(db.String(20), default='pending') # pending, valid, incorrect, ignored
    
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'date'),
        db.Index('idx_user_category', 'user_id', 'category'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': round(float(self.amount), 2) if self.amount is not None else 0.0,
            'description': self.description,
            'category': self.category,
            'date': self.date.strftime('%Y-%m-%d'),
            'payment_method': self.payment_method,
            'notes': self.notes or '',
            'is_recurring': self.is_recurring,
            'predicted_category': self.predicted_category,
            'prediction_confidence': round(self.prediction_confidence, 2) if self.prediction_confidence else None,
            'is_anomaly': self.is_anomaly,
            'anomaly_reason': self.anomaly_reason or '',
            'anomaly_status': self.anomaly_status,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Expense {self.description} - {self.amount}>'
