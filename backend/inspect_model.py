import joblib
import os
from django.conf import settings
import sys

# Add backend to path to import settings if needed, or just hardcode for this quick check
sys.path.append('/home/hannan-ali/Web_App_Scanner/backend')

model_path = '/home/hannan-ali/Web_App_Scanner/ML/fp_confidence_random_forest.pkl'

try:
    model = joblib.load(model_path)
    print("Model loaded successfully.")
    
    if hasattr(model, 'feature_names_in_'):
        print("Expected Features:", model.feature_names_in_)
    else:
        print("Model does not store feature names (older sklearn?).")
        # Try to infer from n_features_in_
        print(f"Number of input features expected: {model.n_features_in_}")

except Exception as e:
    print(f"Error loading model: {e}")
