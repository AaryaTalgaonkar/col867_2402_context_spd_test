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
    """Load CSV, skip the header row, and extract features and labels."""
    df = pd.read_csv(csv_file, header=None, skiprows=1)  # skip header row
    X = df.iloc[:, :-1].values  # All columns except last as features
    y = df.iloc[:, -1].values   # Last column as labels
    return X, y

def split_data(X, y):
    """Perform an 80-20 train-validation split maintaining label distribution."""
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


def split_up_down(X: pd.DataFrame, y: pd.Series):
    # 3rd and 4th columns (0-indexed: cols 2 and 3)
    up_mask = X.iloc[:, 2] > X.iloc[:, 3]
    down_mask = ~up_mask  # or X.iloc[:, 2] <= X.iloc[:, 3]

    # Odd and even column indices (1-indexed)
    odd_cols = [i for i in range(X.shape[1]) if i % 2 == 0]   # 0, 2, 4, ...
    even_cols = [i for i in range(X.shape[1]) if i % 2 == 1]  # 1, 3, 5, ...

    # Apply masks and column selection
    X_up = X.loc[up_mask, X.columns[odd_cols]]
    y_up = y.loc[up_mask]

    X_down = X.loc[down_mask, X.columns[even_cols]]
    y_down = y.loc[down_mask]

    return X_down, X_up, y_down, y_up


if __name__ == "__main__":
    
    CSV_FILE = "features.csv"  # Change this to your actual file path
    X, y = load_data(CSV_FILE)

    X_down, X_up, y_down, y_up = split_up_down(X,y)

    X_train_down, X_val_down, y_train_down, y_val_down = split_data(X_down, y_down)

    model_down = Model()
    model_down.train(X_train_down, y_train_down)
    y_pred_down = model_down.predict(X_val_down)
    metrics = model_down.evaluate(y_pred_down, y_val_down)
    
    print("Evaluation Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    model_down.save_confusion_matrix(y_pred_down, y_val_down, "confusion_matrix_down.png")

    X_train_up, X_val_up, y_train_up, y_val_up = split_data(X_up, y_up)

    model_up = Model()
    model_up.train(X_train_up, y_train_up)
    y_pred_up = model_up.predict(X_val_up)
    metrics = model_up.evaluate(y_pred_up, y_val_up)
    
    print("Evaluation Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    model_up.save_confusion_matrix(y_pred_up, y_val_up, "confusion_matrix_up.png")
