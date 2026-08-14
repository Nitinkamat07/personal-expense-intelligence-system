from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.expense import Expense
from models.budget import Budget
from models.insight import Insight

__all__ = ['db', 'User', 'Expense', 'Budget', 'Insight']
