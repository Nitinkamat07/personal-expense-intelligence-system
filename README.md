# Personal Expense Intelligence System

> **Resume-Quality Full-Stack Financial Analytics & ML System**

Personal Expense Intelligence is a comprehensive web application designed to track, analyze, and forecast personal financial behavior. It incorporates a reproducible Machine Learning classification pipeline, multidimensional anomaly detection, backtested time-series forecasting, and an offline query processor (Spending Copilot) to deliver concrete, accurate insights without relying on third-party APIs.

---

## 🚀 Live Demo

**[View Live Demo](https://personalexpenseintelligencesystem.vercel.app/login?next=%2F)**

---

## 🌟 Key Features

### 🧠 1. Intelligent ML Expense Categorization
- **NLP Text Classification**: Utilizes a TF-IDF vectorizer and a Logistic Regression classifier trained on a structured dataset of transaction descriptions.
- **Reproducible Pipeline**: Includes a CLI training script (`ml/train_categorizer.py`) that preprocesses descriptions, splits the dataset, fits the model, prints validation metrics, and persists the pipeline.
- **Confidence Scoring**: Estimates prediction probabilities using `.predict_proba()`. Auto-suggests predictions with confidence scores in real-time, defaulting to manual confirmation if confidence falls below 40%.

### ⚠️ 2. Multidimensional Anomaly Detection
- **Statistical Z-Score & IQR**: Flags category-specific spending surges (e.g., normal rent vs. abnormal restaurant expenses) based on historical category statistics.
- **Isolation Forest Classifier**: Employs an `IsolationForest` ensemble model utilizing multidimensional features:
  - Transaction Amount
  - Day of the Week (0-6)
  - Day of the Month (1-31)
  - Category (encoded index)
- **Natural Language Explanations**: Provides granular reasoning explaining why a transaction was flagged as an outlier based on historical patterns.

### 📈 3. Backtested Time-Series Forecasting
- **Linear Trend Regression**: Projects current-month spending totals by fitting a linear regression line over daily cumulative spending velocity.
- **Backtesting & Evaluation**: Validates the category weighted moving average model against a **Naive previous-month spending baseline**.
- **Performance Metrics**: Computes **Mean Absolute Error (MAE)** and **Root Mean Squared Error (RMSE)** for both the model and the baseline when sufficient history (3+ months) is present. Renders data-scarcity warnings otherwise.

### 💬 4. Spending Copilot (Deterministic NLP Router)
- **Zero-Hallucination Assistant**: An offline natural language query processor that answers financial questions by running exact database calculations:
  - *"Where did I spend the most money this month?"* (Category spending breakdown)
  - *"Why did I spend more this month?"* (MoM comparison and category cost-driver analysis)
  - *"How much budget is left?"* (Overall budget utilization and category threshold checks)
  - *"Show me my subscriptions."* (Active recurring monthly commitments)

### 📊 5. Financial Dashboard & Alerts
- Interactive charts powered by **Chart.js**: daily velocity trend lines, category doughnut breakdowns, and 6-month historical comparison bars.
- Set overall budgets and category allocations. Dynamic warning states activate at **80% utilization** (warning) and **100% utilization** (overrun).

### 📁 6. CSV Import / Export Center
- Normalizes variations in CSV headers (e.g., transaction_date, value, mode).
- Deduplicates rows using transaction hashes, runs missing categories through the ML auto-suggest model, and checks for anomaly flags during ingestion.

---

## 🛠️ Technology Stack

* **Backend Framework**: Python 3.12+, Flask 3.0, Flask-Login, Flask-WTF (CSRF Protection)
* **Database & ORM**: SQLite 3, SQLAlchemy ORM with Numeric financial precision
* **Machine Learning / Data**: Scikit-learn, Pandas, NumPy, Joblib
* **Frontend Framework**: HTML5, CSS3, Vanilla ES6+ JS, Bootstrap 5.3
* **Data Visualization**: Chart.js 4.4
* **Testing & CI/CD**: Pytest, GitHub Actions

---

## 📐 Project Architecture

```text
personal-expense-intelligence/
├── app.py                      # Flask Application Factory & Blueprints
├── config.py                   # Environment Config & Production Decoupling
├── seed.py                     # Database Seeding & Mock Data Generation
├── requirements.txt            # Python Dependencies
├── .env.example                # Template for environment variables
├── .gitignore                  # Git Ignore configuration
│
├── .github/
│   └── workflows/
│       └── tests.yml           # GitHub Actions CI Workflow
│
├── models/                     # Database Models (Financial Precision)
│   ├── __init__.py
│   ├── user.py                 # User (Auth, Hashed Passwords, Budget)
│   ├── expense.py              # Expense (Numeric Amount, ML Flags, Anomaly Logs)
│   ├── budget.py               # Category Budgets (Numeric Amount)
│   └── insight.py              # Dynamic Alerts (warning, tip, positive)
│
├── routes/                     # Blueprint API Endpoints
│   ├── auth.py                 # Registration, Sessions, Profile
│   ├── expenses.py             # Expense CRUD & Categorization Preview
│   ├── budgets.py              # Target Allocation Management
│   ├── insights.py             # Forecast, Anomaly Actions, insights
│   ├── copilot.py              # Spending Copilot Query Router
│   ├── csv_io.py               # CSV Upload & Export payload handlers
│   └── dashboard.py            # Aggregated Metrics & Charts API
│
├── services/                   # Analytics, ML Models & Core Logic
│   ├── categorizer.py          # TF-IDF + Logistic Regression Wrapper
│   ├── anomaly_detector.py     # Isolation Forest & Z-Score Anomaly Engine
│   ├── forecasting.py          # Linear Regression & Backtesting Evaluator
│   ├── copilot_service.py      # Spending Copilot Local Math Solver
│   ├── insight_engine.py       # Rule-Based Intelligent Insight Engine
│   └── csv_service.py          # CSV Validation, Deduplication & Parse
│
├── templates/                  # Jinja2 Layouts
│   ├── base.html               # Main Sidebar Navigation
│   ├── dashboard.html          # Metric Cards & Chart Layout
│   ├── expenses.html           # Table Controls & CRUD Modals
│   ├── budgets.html            # Progress Bars & Allocations
│   ├── insights.html           # Forecast Cards & Anomalies Center
│   ├── copilot.html            # Chat interface for Copilot Terminal
│   └── import_export.html      # CSV Upload Dropzone
│
├── ml/                         # ML Model persistence
│   ├── train_categorizer.py    # reproducible model training script
│   └── models/                 # Model pickles & metrics files
│
├── data/
│   └── sample_transactions.csv # Base training dataset (154 descriptions)
│
└── tests/                      # Automated Pytest Suite
    ├── test_auth.py            # Auth & Registration
    ├── test_expenses.py        # CRUD, Isolation & Input Validation
    ├── test_budgets_csv.py     # Budgets & CSV Service
    ├── test_ml.py              # ML Categorizer, Anomalies & Forecast backtest
    └── test_copilot.py         # Copilot Service & Route checks
```

---

## 🤖 ML Pipeline & Evaluation Metrics

### 1. ML Categorizer Metrics
When trained on the provided `sample_transactions.csv` (154 transactions across 10 classes), the TF-IDF Vectorizer + Calibrated LinearSVC (C=1.0, balanced class weights) model achieves the following actual evaluation metrics (stratified 20% validation split):

* **Accuracy**: `54.84%`
* **Macro Precision**: `0.4492`
* **Macro Recall**: `0.4967`
* **Macro F1-Score**: `0.4505`
* **Weighted F1-Score**: `0.4997`

> [!NOTE]
> Since transaction descriptions are short and sparse, these baseline metrics represent a clean starting point. A key resume talking-point is dataset size expansion, hyperparameter optimization, or transitioning to pre-trained transformer embeddings.

### 2. Backtesting Forecast Evaluation
The system evaluates the **Weighted Moving Average** forecast against the **Naive baseline model** (predicting that the next month's spending equals the current month's spending) by executing historical backtests.
- If history is $<3$ months, the system displays a warning: `"Not enough historical data for reliable forecasting."`
- Otherwise, it reports actual comparative metrics: **MAE (Mean Absolute Error)** and **RMSE (Root Mean Squared Error)**.

---

## 🛡️ Security Implementations

1. **Decoupled Production Settings**: The system uses `ProductionConfig` when `FLASK_ENV=prod`, enforcing the requirement of a `SECRET_KEY` environment variable.
2. **CSRF Protection**: All forms and AJAX-based state-modifying requests (`POST`, `PUT`, `DELETE`) are guarded using `Flask-WTF` CSRF tokens, passing the token via the `X-CSRFToken` request header.
3. **Data Isolation (Authorization)**: All expense, budget, and insight retrieval queries filter strictly by `current_user.id`. Modifying or deleting records belonging to other users returns an HTTP 404 (Not Found) directly.
4. **Financial Data Precision**: Column definitions use `db.Numeric(12, 2)` instead of floats to eliminate floating-point rounding drifts.

---

## ⚡ Quick Start & Installation

### 1. Setup Environment
```bash
# Clone the repository and navigate inside
cd personal-expense-intelligence

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```text
FLASK_APP=app.py
FLASK_ENV=dev
SECRET_KEY=generate-a-secure-key-here
```

### 3. Seed Database & Train Model
Run the seeding script to compile the database tables, train the ML model, and seed a demo account with **120+ multi-month transactions**:
```bash
python seed.py
```

### 4. Run the Application
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.
- **Demo Email**: `demo@expense.ai`
- **Demo Password**: `password123`

---

## 🧪 Running Tests

Run `pytest` to execute all 17 unit and integration tests:
```bash
pytest -v
```

---

## 🔌 API Endpoint Documentation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/register` | Register a new user |
| `POST` | `/login` | Authenticate user & open session |
| `GET` | `/api/dashboard` | Fetch aggregate data & Chart.js payloads |
| `GET` | `/api/expenses` | Get filtered expenses (search, category, date range) |
| `POST` | `/api/expenses` | Record a new expense (runs categorizer & anomaly checks) |
| `PUT` | `/api/expenses/<id>` | Update an existing expense (checks ownership) |
| `DELETE` | `/api/expenses/<id>` | Delete an expense (checks ownership) |
| `POST` | `/api/copilot` | Submit query to the offline Spending Copilot |
| `GET` | `/api/budgets` | Fetch monthly target allocations & progress stats |
| `POST` | `/api/budgets` | Set or update category budget limit |
| `GET` | `/api/forecast` | Retrieve linear model monthly spending projections |
| `GET` | `/api/anomalies` | Get list of flagged unusual transactions |
| `POST` | `/api/anomalies/<id>/feedback` | Record user feedback (valid/incorrect/ignored) |
| `POST` | `/api/import` | Upload & parse CSV expense file |
| `GET` | `/api/export` | Download expense records as CSV file |
