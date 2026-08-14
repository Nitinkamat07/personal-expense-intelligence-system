import os
import json
import re
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)
import joblib

def clean_text_advanced(text):
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    # Remove transactional noise e.g., txn IDs, check numbers, UPI references, dates
    text = re.sub(r'\btxn\b|\bref\b|\bchq\b|\bchqno\b|\brefno\b|\bval\b', ' ', text)
    text = re.sub(r'\b[a-z]{2,3}-\d+\b', ' ', text)
    text = re.sub(r'\b\d{6,}\b', ' ', text)
    text = re.sub(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return ' '.join(text.split())

def train_and_evaluate(data_path='data/sample_transactions.csv', model_dir='ml/models'):
    print(f"Loading training data from {data_path}...")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data file not found at: {data_path}")

    df = pd.read_csv(data_path)
    
    # Validate columns
    if 'Description' not in df.columns or 'Category' not in df.columns:
        raise ValueError("CSV must contain 'Description' and 'Category' columns.")

    print(f"Pre-processing descriptions ({len(df)} records)...")
    X = df['Description'].apply(clean_text_advanced).tolist()
    y = df['Category'].tolist()

    # Stratified Split (80-20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Building TF-IDF + Calibrated LinearSVC pipeline...")
    # Wrap LinearSVC inside CalibratedClassifierCV to get predict_proba support (using cv=3 due to sample sizes)
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ('clf', CalibratedClassifierCV(
            estimator=LinearSVC(C=1.0, class_weight='balanced', random_state=42),
            cv=3
        ))
    ])

    print("Training the pipeline...")
    pipeline.fit(X_train, y_train)

    print("Evaluating model performance on test split...")
    y_pred = pipeline.predict(X_test)

    # Calculate overall metrics
    accuracy = accuracy_score(y_test, y_pred)
    p_macro, r_macro, f_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro', zero_division=0)
    p_weighted, r_weighted, f_weighted, _ = precision_recall_fscore_support(y_test, y_pred, average='weighted', zero_division=0)

    print("\n================ ML Model Evaluation Metrics ================")
    print(f"Accuracy:          {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"Macro Precision:   {p_macro:.4f}")
    print(f"Weighted Precision:{p_weighted:.4f}")
    print(f"Macro Recall:      {r_macro:.4f}")
    print(f"Weighted Recall:   {r_weighted:.4f}")
    print(f"Macro F1-Score:    {f_macro:.4f}")
    print(f"Weighted F1-Score: {f_weighted:.4f}")
    print("=============================================================\n")

    print("\nClassification Report:")
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    print(classification_report(y_test, y_pred, zero_division=0))

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Persist the model
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'category_model.pkl')
    print(f"Saving model pipeline to {model_path}...")
    joblib.dump(pipeline, model_path)
    
    # Save a JSON file with comprehensive metrics
    metrics_path = os.path.join(model_dir, 'metrics.json')
    
    # Extract per-class metrics
    per_class_metrics = {}
    for key, val in report_dict.items():
        if key not in ['accuracy', 'macro avg', 'weighted avg']:
            per_class_metrics[key] = {
                'precision': float(val['precision']),
                'recall': float(val['recall']),
                'f1-score': float(val['f1-score']),
                'support': int(val['support'])
            }

    metrics_payload = {
        'model_name': 'Calibrated LinearSVC (C=1.0, balanced, TF-IDF ngram_range=(1,2), sublinear_tf=True)',
        'dataset_size': len(df),
        'number_of_classes': int(df['Category'].nunique()),
        'accuracy': float(accuracy),
        'macro_precision': float(p_macro),
        'macro_recall': float(r_macro),
        'macro_f1': float(f_macro),
        'f1_macro': float(f_macro),
        'weighted_precision': float(p_weighted),
        'weighted_recall': float(r_weighted),
        'weighted_f1': float(f_weighted),
        'f1_weighted': float(f_weighted),
        'per_class_metrics': per_class_metrics,
        'trained_at': pd.Timestamp.now().isoformat()
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics_payload, f, indent=4)
        
    print("Model training pipeline execution complete!")
    return accuracy, f_macro

if __name__ == '__main__':
    train_and_evaluate()
