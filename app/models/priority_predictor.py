from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class PriorityPredictor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = RandomForestClassifier(n_estimators=100)
        self.is_trained = False

    def train(self, task_descriptions, priorities):
        """
        Train the model with task descriptions and their priorities
        """
        X = self.vectorizer.fit_transform(task_descriptions)
        self.classifier.fit(X, priorities)
        self.is_trained = True

    def predict_priority(self, task_description):
        """
        Predict the priority of a new task based on its description
        """
        if not self.is_trained:
            return 3  # Default priority if model is not trained
        
        X = self.vectorizer.transform([task_description])
        priority = self.classifier.predict(X)[0]
        return int(priority)

    def get_priority_features(self, task_description):
        """
        Get the most important words for priority prediction
        """
        if not self.is_trained:
            return []
        
        X = self.vectorizer.transform([task_description])
        feature_names = self.vectorizer.get_feature_names_out()
        importance = self.classifier.feature_importances_
        
        # Get top 5 important features
        top_indices = np.argsort(importance)[-5:][::-1]
        return [feature_names[i] for i in top_indices] 