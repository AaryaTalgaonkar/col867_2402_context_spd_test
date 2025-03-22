import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, f1_score, confusion_matrix

class Model:
    def __init__(self, model=None):
        """Initialize the wrapper model with a given internal model."""
        self.model = model if model else RandomForestClassifier(n_estimators=100, random_state=42)

    def train(self, X_train, y_train):
        """Train the internal model."""
        self.model.fit(X_train, y_train)

    def predict(self, X):
        """Predict using the internal model."""
        return self.model.predict(X)

    def evaluate(self, y_pred, y_gold):
        """Compute evaluation metrics."""
        metrics = {
            "accuracy": accuracy_score(y_gold, y_pred),
            "precision_macro": precision_score(y_gold, y_pred, average="macro"),
            "f1_score_macro": f1_score(y_gold, y_pred, average="macro"),
        }
        return metrics
    
    def save_confusion_matrix(self, y_pred, y_gold, file_name):
        """Save confusion matrix as an image file."""
        cm = confusion_matrix(y_gold, y_pred)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=np.unique(y_gold), yticklabels=np.unique(y_gold))
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.title('Confusion Matrix')
        plt.savefig(file_name)
        plt.close()


def load_data(csv_file):
    """Load CSV and extract features and labels."""
    df = pd.read_csv(csv_file)
    X = df.iloc[:, :-1].values  # All columns except last as features
    y = df.iloc[:, -1].values   # Last column as labels
    return X, y


def split_data(X, y):
    """Perform an 80-20 train-validation split maintaining label distribution."""
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


if __name__ == "__main__":
    CSV_FILE = "features.csv"  # Change this to your actual file path
    X, y = load_data(CSV_FILE)
    X_train, X_val, y_train, y_val = split_data(X, y)

    model = Model()
    model.train(X_train, y_train)
    y_pred = model.predict(X_val)
    metrics = model.evaluate(y_pred, y_val)
    
    print("Evaluation Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    model.save_confusion_matrix(y_pred, y_val, "confusion_matrix.png")