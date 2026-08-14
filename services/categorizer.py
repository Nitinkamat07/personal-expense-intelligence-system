import os
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

class ExpenseCategorizer:
    def __init__(self, model_dir='ml/models'):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, 'category_model.pkl')
        self.pipeline = None
        self._load_or_create_pipeline()

    def _clean_text(self, text):
        if not text:
            return ""
        text = str(text).lower()
        # Remove transactional noise e.g., txn IDs, check numbers, UPI references, dates
        text = re.sub(r'\btxn\b|\bref\b|\bchq\b|\bchqno\b|\brefno\b|\bval\b', ' ', text)
        text = re.sub(r'\b[a-z]{2,3}-\d+\b', ' ', text)
        text = re.sub(r'\b\d{6,}\b', ' ', text)
        text = re.sub(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', ' ', text)
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return ' '.join(text.split())

    def _load_or_create_pipeline(self):
        if os.path.exists(self.model_path):
            try:
                self.pipeline = joblib.load(self.model_path)
                return
            except Exception as e:
                print(f"Error loading model from {self.model_path}: {e}")
        
        # Default fallback pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
            ('clf', CalibratedClassifierCV(
                estimator=LinearSVC(C=1.0, class_weight='balanced', random_state=42),
                cv=3
            ))
        ])

    def train(self, descriptions, categories):
        """Train the model with list of description strings and target category labels."""
        cleaned_desc = [self._clean_text(d) for d in descriptions]
        self.pipeline.fit(cleaned_desc, categories)
        
        # Save model
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)
        return True

    def predict(self, description):
        """
        Predict category for a given description string.
        Returns tuple: (predicted_category, confidence_score, is_confident)
        """
        if not description or not hasattr(self.pipeline, 'classes_'):
            return "Other", 0.0, False

        cleaned = self._clean_text(description)
        if not cleaned:
            return "Other", 0.0, False

        try:
            probs = self.pipeline.predict_proba([cleaned])[0]
            max_idx = probs.argmax()
            predicted_class = self.pipeline.classes_[max_idx]
            confidence = float(probs[max_idx])
            
            # Require at least 0.40 confidence to consider it confident
            is_confident = confidence >= 0.40
            return predicted_class, confidence, is_confident
        except Exception as e:
            print(f"Prediction error for '{description}': {e}")
            return "Other", 0.0, False

    def get_metrics(self):
        import json
        metrics_path = os.path.join(self.model_dir, 'metrics.json')
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

# Global instance for easy import
categorizer = ExpenseCategorizer()
